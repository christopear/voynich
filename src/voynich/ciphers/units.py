"""Prefix-free glyph/group/word codes with explicit spelling randomness."""
from dataclasses import dataclass
import random
import string
from .contracts import CipherState, DecodingOutcome, MethodCapabilities
from .models import CipherKey

ALPHABET = string.ascii_letters + string.digits


@dataclass(frozen=True)
class UnitCipher:
    family: str = "glyph"
    homophones: int = 1
    lengths: str = "fixed"
    spacing: str = "preserve"
    extra_units: tuple[str, ...] = ()

    def __post_init__(self):
        if self.family not in {"glyph", "groups", "mixed"}:
            raise NotImplementedError("unsupported cipher family")
        if self.homophones not in {1, 2} or type(self.homophones) is not int:
            raise NotImplementedError("one or two homophones supported")
        if self.lengths not in {"fixed", "variable"} or self.spacing not in {"preserve", "encoded"}:
            raise ValueError("unsupported code lengths or spacing")
        if self.family == "glyph" and (self.lengths != "fixed" or self.extra_units):
            raise ValueError("glyph method requires single-character codes/emissions")
        if not isinstance(self.extra_units, tuple) or len(set(self.extra_units)) != len(self.extra_units):
            raise ValueError("extra units must be a distinct immutable tuple")
        for unit in self.extra_units:
            if len(unit) < 2 or any(c not in string.ascii_lowercase for c in unit):
                raise ValueError("extra units must contain lowercase letters")
            if self.family == "groups" and len(unit) != 2:
                raise ValueError("group units are pairs; use mixed for words")

    @property
    def method_id(self):
        return "prefix-unit-v1"

    @property
    def units(self):
        return tuple(string.ascii_lowercase) + ((" ",) if self.spacing == "encoded" else ()) + self.extra_units

    def capabilities(self):
        return MethodCapabilities()

    def initial_state(self):
        return CipherState()

    def generate_key(self, *, seed: int) -> CipherKey:
        if self.family == "glyph":
            codes = list(ALPHABET)
        elif self.lengths == "fixed":
            codes = [a + b for a in ALPHABET for b in ALPHABET]
        else:
            # The single-character leaves never prefix the two-character leaves.
            codes = list(ALPHABET[:31]) + [a + b for a in ALPHABET[31:] for b in ALPHABET]
        needed = len(self.units) * self.homophones
        if needed > len(codes):
            raise ValueError("code alphabet capacity exceeded")
        rng = random.Random(seed)
        rng.shuffle(codes)
        if self.lengths == "variable":
            # Guarantee both lengths, independent of plaintext, for matrix coverage.
            singles = [c for c in codes if len(c) == 1]
            pairs = [c for c in codes if len(c) == 2]
            codes = [singles.pop(), pairs.pop()] + singles + pairs
        entries = tuple((codes[i], unit) for i, unit in enumerate(
            unit for unit in self.units for _ in range(self.homophones)))
        key = CipherKey(self.method_id, entries)
        self.validate_key(key)
        return key

    def validate_key(self, key: CipherKey) -> None:
        if key.cipher_id != self.method_id:
            raise ValueError("method/key mismatch")
        mapping = key.as_mapping()
        if set(mapping.values()) != set(self.units):
            raise ValueError("key emissions do not match configured inventory")
        if any(list(mapping.values()).count(unit) != self.homophones for unit in self.units):
            raise ValueError("incorrect homophone count")
        codes = sorted(mapping)
        if any(any(c not in ALPHABET for c in code) for code in codes):
            raise ValueError("codes must be ASCII alphanumeric")
        if any(b.startswith(a) for a, b in zip(codes, codes[1:])):
            raise ValueError("reference cipher requires prefix-free codes")
        if self.family == "glyph" and any(len(c) != 1 for c in codes):
            raise ValueError("glyph codes must be length one")
        if self.family != "glyph":
            if any(len(c) not in {1, 2} for c in codes):
                raise ValueError("group codes must be length one or two")
            if self.lengths == "fixed" and any(len(c) != 2 for c in codes):
                raise ValueError("fixed grouped codes must be length two")

    def encrypt_text(self, text: str, key: CipherKey, *, seed: int = 0):
        self.validate_key(key)
        if not text or any(c not in string.ascii_lowercase + " " for c in text):
            raise ValueError("plaintext must be nonempty normalized lowercase text")
        options = {u: sorted(c for c, v in key.entries if v == u) for u in self.units}
        rng = random.Random(seed)
        units = sorted(self.units, key=lambda u: (-len(u), u))
        output, alignment = [], []
        start = pos = 0
        while pos < len(text):
            if text[pos] == " " and self.spacing == "preserve":
                unit = code = " "
            else:
                available = [u for u in units if text.startswith(u, pos) and
                    (len(u) <= 2 or ((pos == 0 or text[pos-1] == " ") and
                                     (pos+len(u) == len(text) or text[pos+len(u)] == " ")))]
                if not available:
                    raise ValueError("key cannot encode plaintext")
                unit = available[0]
                code = rng.choice(options[unit])
            output.append(code)
            alignment.append((pos, pos + len(unit), start, start + len(code)))
            start += len(code)
            pos += len(unit)
        return "".join(output), tuple(alignment)

    def decrypt_text(self, text: str, key: CipherKey) -> DecodingOutcome:
        """Independent trie traversal; never uses encryption alignment or an LM."""
        self.validate_key(key)
        if not text:
            raise ValueError("empty ciphertext")
        trie = {}
        for code, unit in key.entries:
            node = trie
            for char in code:
                node = node.setdefault(char, {})
            node[None] = unit
        result, pos = [], 0
        while pos < len(text):
            if text[pos] == " " and self.spacing == "preserve":
                result.append(" ")
                pos += 1
                continue
            node, end = trie, pos
            while end < len(text) and text[end] in node:
                node = node[text[end]]
                end += 1
                if None in node:
                    break
            if None not in node:
                return DecodingOutcome((), "no-valid-path", pos / len(text), 0, False)
            result.append(node[None])
            pos = end
        return DecodingOutcome(("".join(result),), "unique-plaintext", 1.0, 1, True)
