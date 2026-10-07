from __future__ import annotations

import hashlib
import math
import random
import re
import string
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache


def normalize(text: str) -> str:
    """Explicit accent folding; keep i/j and u/v distinct. Not a diplomatic edition."""
    text = text.lower().replace("æ", "ae").replace("œ", "oe")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.sub("[^a-z ]", " ", text).split())


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class LanguageModel:
    """Interpolated character n-grams, with normalized conditional distributions."""

    alphabet = string.ascii_lowercase + " "

    def __init__(self, text: str, order: int = 4):
        if not 1 <= order <= 6:
            raise ValueError("order must be between 1 and 6")
        self.text = normalize(text)
        if len(self.text) < 100:
            raise ValueError("language training text must contain at least 100 characters")
        self.order = order
        self.counts = defaultdict(Counter)
        self.totals = Counter()
        history = "^" * (order - 1)
        for char in self.text:
            for size in range(order):
                context = history[-size:] if size else ""
                self.counts[context][char] += 1
                self.totals[context] += 1
            history = (history + char)[-(order - 1):] if order > 1 else ""
        self.words = Counter(self.text.split())

    @lru_cache(maxsize=250_000)
    def cost(self, history: str, char: str) -> float:
        if char not in self.alphabet:
            raise ValueError(f"unsupported plaintext character: {char!r}")
        probability = 1 / len(self.alphabet)
        for size in range(self.order):
            context = history[-size:] if size else ""
            total = self.totals.get(context, 0)
            probability = (self.counts.get(context, {}).get(char, 0) + 5 * probability) / (total + 5)
        return -math.log2(probability)

    def extend(self, history: str, emission: str) -> tuple[float, str]:
        cost = 0.0
        for char in emission:
            cost += self.cost(history, char)
            history = (history + char)[-(self.order - 1):] if self.order > 1 else ""
        return cost, history

    def nll(self, text: str) -> float:
        return self.extend("^" * (self.order - 1), text)[0]


@dataclass(frozen=True)
class Config:
    family: str = "glyph"
    spacing: str = "preserve"
    order: int = 4
    steps: int = 2000
    restarts: int = 4
    beam: int = 8
    max_code_length: int = 3
    extra_codes: int = 12
    pair_units: int = 8
    word_units: int = 8
    temperature_start: float = 12.0
    temperature_end: float = 0.2
    key_weight: float = 1.0
    min_ratio: float = 0.2
    max_ratio: float = 3.0
    keep: int = 5
    seed: int = 20260930

    def validate(self):
        if self.family not in {"glyph", "groups", "mixed"}:
            raise ValueError("family must be glyph, groups, or mixed")
        if self.spacing not in {"preserve", "infer"}:
            raise ValueError("spacing must be preserve or infer")
        if min(self.steps, self.restarts, self.beam, self.keep) < 1:
            raise ValueError("steps, restarts, beam and keep must be positive")
        if not 1 <= self.order <= 6 or not 1 <= self.max_code_length <= 5:
            raise ValueError("order must be 1..6; max_code_length must be 1..5")
        if min(self.extra_codes, self.pair_units, self.word_units, self.key_weight) < 0:
            raise ValueError("inventory limits and key weight must be nonnegative")
        if not 0 < self.temperature_end <= self.temperature_start:
            raise ValueError("temperatures must satisfy 0 < end <= start")
        if not 0 < self.min_ratio <= self.max_ratio:
            raise ValueError("invalid plaintext/ciphertext length ratio bounds")


def prepare_cipher(text: str, spacing: str) -> str:
    # Explicit plain-text input only. Never silently remove IVTFF annotations.
    text = " ".join(text.split())
    if not text or re.search(r"[^a-zA-Z0-9 ]", text):
        raise ValueError("cipher input must be a nonempty plain ASCII letter/digit transcription; annotations must be resolved explicitly")
    return text if spacing == "preserve" else text.replace(" ", "")


def inventory(lm: LanguageModel, cfg: Config) -> list[str]:
    units = list(string.ascii_lowercase)
    if cfg.spacing == "infer":
        units.append(" ")
    if cfg.family != "glyph":
        pairs = Counter(lm.text[i:i + 2] for i in range(len(lm.text) - 1)
                        if " " not in lm.text[i:i + 2])
        units += [p for p, _ in pairs.most_common(cfg.pair_units)]
    if cfg.family == "mixed":
        words = [w for w, _ in lm.words.most_common() if len(w) >= 3][:cfg.word_units]
        # Infer mode word codes carry their own explicit word boundaries.
        units += [f" {w} " if cfg.spacing == "infer" else w for w in words]
    return sorted(set(units))


def candidate_codes(cipher: str, cfg: Config) -> list[str]:
    counts = Counter()
    for word in cipher.split():
        for n in range(2, cfg.max_code_length + 1):
            counts.update(word[i:i + n] for i in range(len(word) - n + 1))
    # This is a bounded inventory, not exhaustive coverage of all codebooks.
    return [code for code, n in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
            if n >= 2][:max(32, cfg.extra_codes * 4)]


def key_bits(key: dict[str, str], unit_count: int, cipher_alphabet: int) -> float:
    # Declared description-length surrogate, not a calibrated prior.
    return math.log2(len(key) + 1) + sum(
        math.log2(len(code) + 1) + len(code) * math.log2(max(2, cipher_alphabet))
        + math.log2(unit_count) for code in key)


def decode(cipher: str, key: dict[str, str], lm: LanguageModel, beam: int,
           word_boundaries: bool = False) -> dict:
    """Best bounded-beam path; consume every symbol exactly, without nulls.

    Scores include uniform choice among the key's codes for each emission.
    This is a Viterbi-style path score, not marginalized model evidence.
    """
    if not key or any(not c or not u or " " in c for c, u in key.items()):
        raise ValueError("codes/emissions must be nonempty; code strings cannot contain spaces")
    variants = Counter(key.values())
    grouped = defaultdict(list)
    for code, emission in sorted(key.items()):
        grouped[code[0]].append((code, emission, math.log2(variants[emission])))
    # (total path cost, plaintext, consumed codes, history, language cost)
    start = (0.0, "", (), "^" * (lm.order - 1), 0.0)
    states = {0: [start]}
    for pos in range(len(cipher)):
        current = sorted(states.pop(pos, []), key=lambda x: (x[0], x[1], x[2]))[:beam]
        if not current:
            continue
        options = [(" ", " ", 0.0)] if cipher[pos] == " " else grouped.get(cipher[pos], [])
        for code, emission, choice_cost in options:
            if not cipher.startswith(code, pos):
                continue
            end = pos + len(code)
            if word_boundaries and len(emission) > 2 and " " not in emission:
                if (pos and cipher[pos - 1] != " ") or (end < len(cipher) and cipher[end] != " "):
                    continue
            target = states.setdefault(end, [])
            for cost, plain, path, history, language in current:
                added, hist = lm.extend(history, emission)
                target.append((cost + added + choice_cost, plain + emission,
                               path + (code,), hist, language + added))
            if len(target) > beam * 4:
                states[end] = sorted(target, key=lambda x: (x[0], x[1], x[2]))[:beam]
    ends = states.get(len(cipher), [])
    if not ends:
        return {"valid": False, "reason": "uncovered cipher symbols", "unknown_symbols": sorted(set(cipher) - set(" ") - set(c[0] for c in key))}
    best = min(ends, key=lambda x: (x[0], x[1], x[2]))
    cost, plaintext, path, _, language = best
    assert "".join(path) == cipher
    return {"valid": True, "plaintext": plaintext, "path": list(path),
            "path_bits": cost, "language_bits": language,
            "encoding_choice_bits": cost - language,
            "plaintext_characters": len(plaintext), "exact_cipher_coverage": True}


def evaluate(cipher: str, key: dict[str, str], lm: LanguageModel, cfg: Config, units: list[str]) -> dict:
    result = decode(cipher, key, lm, cfg.beam,
                    word_boundaries=cfg.family == "mixed" and cfg.spacing == "preserve")
    if not result["valid"]:
        return result
    count = len(cipher.replace(" ", ""))
    ratio = len(result["plaintext"].replace(" ", "")) / count
    if not cfg.min_ratio <= ratio <= cfg.max_ratio:
        return {"valid": False, "reason": "length ratio outside declared bounds", "ratio": ratio}
    complexity = key_bits(key, len(units), len(set(cipher) - {" "}))
    result.update(key_bits=complexity, score=result["path_bits"] + cfg.key_weight * complexity,
                  score_per_cipher_symbol=(result["path_bits"] + cfg.key_weight * complexity) / count,
                  plaintext_ratio=ratio, key=dict(sorted(key.items())))
    return result


def initial_key(cipher: str, lm: LanguageModel, rng: random.Random, restart: int) -> dict[str, str]:
    codes = [c for c, _ in Counter(cipher.replace(" ", "")).most_common()]
    letters = [c for c, _ in Counter(lm.text.replace(" ", "")).most_common()]
    letters += [c for c in string.ascii_lowercase if c not in letters]
    if restart:
        rng.shuffle(letters)
    return {c: letters[i % len(letters)] for i, c in enumerate(codes)}


def mutate(key: dict[str, str], codes: list[str], units: list[str], cfg: Config,
           rng: random.Random) -> dict[str, str]:
    out = dict(key)
    extra = [c for c in out if len(c) > 1]
    move = rng.random()
    if cfg.family != "glyph" and move < 0.15:
        available = [c for c in codes if c not in out]
        if available and len(extra) < cfg.extra_codes:
            out[rng.choice(available)] = rng.choice(units)
    elif cfg.family != "glyph" and move < 0.25 and extra:
        del out[rng.choice(extra)]
    elif move < 0.65 and len(out) > 1:
        a, b = rng.sample(list(out), 2)
        out[a], out[b] = out[b], out[a]
    else:
        out[rng.choice(list(out))] = rng.choice(units)
    return out


def search_restart(cipher: str, training: str, cfg: Config, restart: int) -> dict:
    cfg.validate()
    lm = LanguageModel(training, cfg.order)
    cipher = prepare_cipher(cipher, cfg.spacing)
    units = inventory(lm, cfg)
    codes = candidate_codes(cipher, cfg) if cfg.family != "glyph" else []
    rng = random.Random(cfg.seed + 104729 * restart)
    key = initial_key(cipher, lm, rng, restart)
    current = evaluate(cipher, key, lm, cfg, units)
    if not current["valid"]:
        raise ValueError("initial key invalid under ratio bounds")
    archive = {}

    def remember(result):
        signature = tuple(sorted(result["key"].items()))
        archive[signature] = result
        if len(archive) > cfg.keep:
            del archive[max(archive, key=lambda k: archive[k]["score"])]

    remember(current)
    accepted, invalid = 0, 0
    trace = []
    for step in range(cfg.steps):
        proposal = mutate(key, codes, units, cfg, rng)
        candidate = evaluate(cipher, proposal, lm, cfg, units)
        temperature = cfg.temperature_start * (cfg.temperature_end / cfg.temperature_start) ** (step / max(1, cfg.steps - 1))
        if candidate["valid"]:
            remember(candidate)
            delta = candidate["score"] - current["score"]
            if delta <= 0 or rng.random() < 2 ** (-delta / temperature):
                key, current = proposal, candidate
                accepted += 1
        else:
            invalid += 1
        if step == 0 or (step + 1) % max(1, cfg.steps // 20) == 0:
            trace.append({"step": step + 1, "temperature": temperature,
                          "best_score": min(x["score"] for x in archive.values())})
    return {"restart": restart, "seed": cfg.seed + 104729 * restart,
            "evaluations": cfg.steps + 1, "accepted": accepted, "invalid": invalid,
            "trace": trace, "candidates": sorted(archive.values(), key=lambda x: x["score"])}


def synthetic(plaintext: str, family: str, seed: int, homophones: int = 1,
              allowed_units: list[str] | None = None) -> tuple[str, dict, list]:
    """Known-key fixture. Group codes are fixed-width here, not all search cases."""
    if family not in {"glyph", "groups", "mixed"} or homophones not in {1, 2}:
        raise ValueError("unsupported synthetic family/homophone count")
    rng = random.Random(seed)
    plain = normalize(plaintext)
    words = plain.split()
    frequent = {w for w, _ in Counter(words).most_common(8) if len(w) >= 3}
    if allowed_units is not None:
        frequent = {u for u in allowed_units if len(u) >= 3}
    sequence = []
    for index, word in enumerate(words):
        if index:
            sequence.append(" ")
        if family == "mixed" and word in frequent:
            sequence.append(word)
        elif family != "glyph":
            i = 0
            while i < len(word):
                pair = word[i:i + 2]
                unit = pair if allowed_units is None or pair in allowed_units else word[i]
                sequence.append(unit)
                i += len(unit)
        else:
            sequence.extend(word)
    units = sorted(set(sequence) - {" "})
    alphabet = string.ascii_letters + string.digits
    pool = list(alphabet) if family == "glyph" else [a + b for a in alphabet for b in alphabet]
    rng.shuffle(pool)
    if len(units) * homophones > len(pool):
        raise ValueError("synthetic code inventory exhausted")
    key, options = {}, {}
    for unit in units:
        options[unit] = [pool.pop() for _ in range(homophones)]
        for code in options[unit]:
            key[code] = unit
    path = [" " if u == " " else rng.choice(options[u]) for u in sequence]
    return "".join(path), key, path


def edit_accuracy(prediction: str, truth: str) -> float:
    row = list(range(len(truth) + 1))
    for i, a in enumerate(prediction, 1):
        new = [i]
        for j, b in enumerate(truth, 1):
            new.append(min(new[-1] + 1, row[j] + 1, row[j - 1] + (a != b)))
        row = new
    return max(0.0, 1 - row[-1] / max(1, len(truth)))
