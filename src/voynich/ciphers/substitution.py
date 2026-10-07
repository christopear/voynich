"""Reference character cipher and an independent, language-model-free decoder."""
import random
import string

from voynich.decipher_search.core import normalize

from .api import Decryption, Encryption
from .models import (CipherKey, Ciphertext, DecryptionResult, EncryptedFixture,
                     PreparedText, TextSource)

SCHEME = "character-homophonic-v1"
NORMALIZATION = "ascii-fold-ae-oe-preserve-ij-uv-v1"


def validate_key(key: CipherKey) -> dict[str, str]:
    if key.cipher_id != SCHEME:
        raise ValueError("key belongs to an unsupported cipher scheme")
    mapping = key.as_mapping()
    alphabet = string.ascii_letters + string.digits
    if any(len(code) != 1 or code not in alphabet or len(unit) != 1 or
           unit not in string.ascii_lowercase for code, unit in mapping.items()):
        raise ValueError("reference keys map one ASCII letter/digit to one lowercase letter")
    return mapping


class SubstitutionEncryption(Encryption):
    def __init__(self, *, homophones: int = 1):
        if type(homophones) is not int or homophones not in (1, 2):
            raise NotImplementedError("reference encryption supports one or two homophones per letter")
        self.homophones = homophones

    def prepare(self, source: TextSource) -> PreparedText:
        if not set(source.languages) <= {"latin", "italian"}:
            raise NotImplementedError("normalization currently supports declared Latin/Italian sources")
        text = normalize(source.text)
        if not text:
            raise ValueError("source has no letters after normalization")
        return PreparedText(text, source, NORMALIZATION)

    def generate_key(self, *, seed: int) -> CipherKey:
        # Full alphabet: held-out plaintext cannot influence key construction.
        codes = list(string.ascii_letters + string.digits)
        random.Random(seed).shuffle(codes)
        entries = tuple((codes.pop(), letter) for letter in string.ascii_lowercase
                        for _ in range(self.homophones))
        return CipherKey(SCHEME, entries)

    def encrypt(self, source: TextSource, *, key: CipherKey | None = None,
                key_seed: int = 0, encryption_seed: int = 0) -> EncryptedFixture:
        plain = self.prepare(source)
        generated = key is None
        key = self.generate_key(seed=key_seed) if generated else key
        mapping = validate_key(key)
        options = {letter: sorted(c for c, u in mapping.items() if u == letter)
                   for letter in string.ascii_lowercase}
        if any(len(codes) != self.homophones for codes in options.values()):
            raise ValueError("supplied key must cover all 26 letters with the configured homophone count")
        rng = random.Random(encryption_seed)
        ciphertext = "".join(" " if c == " " else rng.choice(options[c]) for c in plain.text)
        return EncryptedFixture(Ciphertext(ciphertext, SCHEME), plain, key,
                                key_seed if generated else None, encryption_seed,
                                f"{SCHEME};homophones={self.homophones};spacing=preserve")


class ReferenceDecryption(Decryption):
    def decrypt(self, ciphertext: Ciphertext, *, key: CipherKey) -> DecryptionResult:
        if not isinstance(ciphertext, Ciphertext):
            raise TypeError("pass public Ciphertext, not an EncryptedFixture")
        if ciphertext.cipher_id != key.cipher_id:
            raise ValueError("ciphertext/key scheme mismatch")
        mapping = validate_key(key)
        unknown = set(ciphertext.text) - set(mapping) - {" "}
        if unknown:
            raise ValueError(f"key does not cover cipher symbols: {sorted(unknown)!r}")
        text = "".join(" " if c == " " else mapping[c] for c in ciphertext.text)
        return DecryptionResult(text, "reference-known-key-v1", True)
