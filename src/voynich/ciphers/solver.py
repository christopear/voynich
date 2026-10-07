"""OO adapter to existing bounded search, not a new search implementation."""
from dataclasses import asdict

from voynich.decipher_search.core import Config, LanguageModel, decode

from voynich.search.legacy import legacy_recovery_runs

from .api import Decryption
from .models import (CipherKey, Ciphertext, DecryptionResult, RecoveryCandidate,
                     RecoveryResult, TextSource)
from .substitution import SCHEME, validate_key


class AnnealingDecryption(Decryption):
    def __init__(self, training: TextSource, *, config: Config | None = None):
        self.training = training
        self.config = config or Config()
        self.config.validate()
        if not set(training.languages) <= {"latin", "italian"}:
            raise NotImplementedError("adapter currently supports Latin/Italian training sources")
        if self.config.family != "glyph" or self.config.spacing != "preserve":
            raise NotImplementedError("OO adapter initially supports character codes with preserved spaces")
        self.model = LanguageModel(training.text, self.config.order)

    def _validate(self, ciphertext: Ciphertext):
        if not isinstance(ciphertext, Ciphertext):
            raise TypeError("solver accepts public Ciphertext only, not fixture ground truth")
        if ciphertext.cipher_id != SCHEME:
            raise NotImplementedError("unsupported cipher scheme for this adapter")
        if not ciphertext.text or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 " for c in ciphertext.text):
            raise ValueError("adapter requires nonempty ASCII letter/digit ciphertext")
        if " ".join(ciphertext.text.split()) != ciphertext.text:
            raise ValueError("ciphertext spacing must already be normalized; it is not silently changed")

    def decrypt(self, ciphertext: Ciphertext, *, key: CipherKey) -> DecryptionResult:
        self._validate(ciphertext)
        mapping = validate_key(key)
        result = decode(ciphertext.text, mapping, self.model, self.config.beam)
        if not result["valid"]:
            raise ValueError("key does not completely cover ciphertext")
        return DecryptionResult(result["plaintext"], "explorer-known-key-v1", True)

    def recover(self, ciphertext: Ciphertext) -> RecoveryResult:
        self._validate(ciphertext)
        runs = legacy_recovery_runs(ciphertext.text, self.training.text, self.config)
        candidates = {}
        for run in runs:
            for item in run["candidates"]:
                entries = tuple(sorted(item["key"].items()))
                candidates[entries] = RecoveryCandidate(
                    DecryptionResult(item["plaintext"], "annealing-beam-v1", item["exact_cipher_coverage"]),
                    CipherKey(SCHEME, entries), item["score"], tuple(item["path"]))
        return RecoveryResult(tuple(sorted(candidates.values(), key=lambda c: c.score)[:self.config.keep]),
                              self.training, tuple(sorted(asdict(self.config).items())),
                              sum(r["evaluations"] for r in runs))
