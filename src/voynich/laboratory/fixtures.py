"""Synthetic fixtures: separate public ciphertext and private evaluation truth."""
from dataclasses import asdict, dataclass
from pathlib import Path
from voynich.ciphers.models import TextSource, CipherKey
from voynich.ciphers.substitution import NORMALIZATION
from voynich.ciphers.units import UnitCipher
from voynich.decipher_search.core import normalize, digest, candidate_codes, inventory, LanguageModel, Config
from voynich.laboratory.manifest import stream_seed, fingerprint
from voynich.storage.artifacts import write_json, read_json


@dataclass(frozen=True)
class PublicInput:
    ciphertext: str
    method_id: str
    spacing: str
    role: str = "development"

    def __post_init__(self):
        if self.role not in {"development", "evaluation"}:
            raise ValueError("public input role must be development or evaluation")
        if not self.ciphertext or not self.ciphertext.strip() or self.spacing not in {"preserve", "encoded"}:
            raise ValueError("invalid public ciphertext")

    @classmethod
    def load(cls, path: Path):
        value = read_json(path)
        if value.pop("schema", None) != 1:
            raise ValueError("unsupported public input schema")
        return cls(**value)


@dataclass(frozen=True)
class FixtureTruth:
    plaintext: str
    key: CipherKey
    alignment: tuple
    provenance: dict
    key_seed: int
    encryption_seed: int


@dataclass(frozen=True)
class SyntheticFixture:
    public: PublicInput
    truth: FixtureTruth
    method: UnitCipher
    historical_status: str = "implementation-supported; historical attestation not established"

    def save(self, directory: Path):
        # Directory exclusivity prevents mixing truth/public files from different fixtures.
        directory.mkdir(parents=True, exist_ok=False)
        write_json(directory / "public.json", {"schema": 1, **asdict(self.public)})
        write_json(directory / "truth.json", {"schema": 1, **asdict(self.truth),
                   "method": asdict(self.method), "historical_status": self.historical_status,
                   "public_hash": fingerprint(asdict(self.public))})

    @classmethod
    def load_private(cls, directory: Path):
        public = PublicInput.load(directory / "public.json")
        value = read_json(directory / "truth.json")
        if value.pop("schema", None) != 1 or value.pop("public_hash", None) != fingerprint(asdict(public)):
            raise ValueError("fixture schema or public/truth pairing mismatch")
        method_data = value.pop("method")
        method_data["extra_units"] = tuple(method_data["extra_units"])
        method = UnitCipher(**method_data)
        status = value.pop("historical_status")
        key_data = value["key"]
        value["key"] = CipherKey(key_data["cipher_id"], tuple(tuple(x) for x in key_data["entries"]))
        value["alignment"] = tuple(tuple(x) for x in value["alignment"])
        truth = FixtureTruth(**value)
        method.validate_key(truth.key)
        if digest(truth.plaintext) != truth.provenance["prepared_hash"]:
            raise ValueError("private plaintext hash mismatch")
        return cls(public, truth, method, status)

    def search_space(self, training: str, config: Config) -> dict:
        lm = LanguageModel(training, config.order)
        allowed = set(inventory(lm, config))
        available = set(self.public.ciphertext.replace(" ", ""))
        if config.family != "glyph":
            available.update(candidate_codes(self.public.ciphertext, config))
        observed = {self.public.ciphertext[a:b] for _, _, a, b in self.truth.alignment} - {" "}
        active = [(c, v) for c, v in self.truth.key.entries if c in observed]
        missing_units = sorted({v for _, v in active} - allowed)
        missing_codes = sorted({c for c, _ in active} - available)
        long_count = sum(len(c) > 1 for c, _ in active)
        reasons = []
        if missing_units:
            reasons.append("truth units outside training-derived inventory")
        if missing_codes:
            reasons.append("truth codes absent from bounded candidate inventory")
        if long_count > config.extra_codes:
            reasons.append("truth exceeds extra-code budget")
        if (config.spacing == "preserve") != (self.public.spacing == "preserve"):
            reasons.append("spacing mismatch")
        return {"in_search_space": not reasons, "role": "power-test" if not reasons else "challenge-control",
                "reasons": reasons, "missing_units": missing_units, "missing_codes": missing_codes,
                "scope": "codes actually used in development; unseen held-out codes are assessed separately",
                "inactive_key_codes": len(self.truth.key.entries) - len(active)}


class FixtureBuilder:
    def __init__(self, method: UnitCipher):
        self.method = method

    def prepare(self, source: TextSource, *, start=0, stop=None):
        if not set(source.languages) <= {"latin", "italian"}:
            raise NotImplementedError("Latin/Italian normalization only")
        stop = len(source.text) if stop is None else stop
        if not 0 <= start < stop <= len(source.text):
            raise ValueError("invalid raw source span")
        prepared = normalize(source.text[start:stop])
        if not prepared:
            raise ValueError("no normalized letters")
        return prepared, {"source_id": source.source_id, "languages": list(source.languages),
            "uri": source.uri, "raw_hash": source.sha256, "prepared_hash": digest(prepared),
            "start": start, "stop": stop, "normalization": NORMALIZATION}

    def build(self, source: TextSource, *, seed: int, start=0, stop=None):
        text, provenance = self.prepare(source, start=start, stop=stop)
        key_seed = stream_seed(seed, source.source_id, "key")
        spelling_seed = stream_seed(seed, source.source_id, "encryption")
        key = self.method.generate_key(seed=key_seed)
        cipher, alignment = self.method.encrypt_text(text, key, seed=spelling_seed)
        return SyntheticFixture(PublicInput(cipher, self.method.method_id, self.method.spacing),
            FixtureTruth(text, key, alignment, provenance, key_seed, spelling_seed), self.method)
