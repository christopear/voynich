"""Two roles: reversible construction and decryption/recovery.

No interface downloads text or chooses training/evaluation splits implicitly.
"""
from abc import ABC, abstractmethod

from .models import (CipherKey, Ciphertext, DecryptionResult, EncryptedFixture,
                     PreparedText, RecoveryResult, TextSource)


class Encryption(ABC):
    @abstractmethod
    def prepare(self, source: TextSource) -> PreparedText:
        """Declare normalization and retain original source provenance."""
        raise NotImplementedError

    @abstractmethod
    def generate_key(self, *, seed: int) -> CipherKey:
        """Generate a key without inspecting development or evaluation plaintext."""
        raise NotImplementedError

    @abstractmethod
    def encrypt(self, source: TextSource, *, key: CipherKey | None = None,
                key_seed: int = 0, encryption_seed: int = 0) -> EncryptedFixture:
        """Return a fixture whose truth can be separated from its public input."""
        raise NotImplementedError


class Decryption(ABC):
    @abstractmethod
    def decrypt(self, ciphertext: Ciphertext, *, key: CipherKey) -> DecryptionResult:
        """Decode using a supplied key; do not silently refit missing assignments."""
        raise NotImplementedError

    def recover(self, ciphertext: Ciphertext) -> RecoveryResult:
        """Unknown-key search is optional and must never default to oracle decoding."""
        raise NotImplementedError(f"{type(self).__name__} does not implement unknown-key recovery")
