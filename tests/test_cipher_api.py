"""Public API contracts; broad recovery-power calibration remains separate."""
from dataclasses import asdict, FrozenInstanceError
from pathlib import Path
import tempfile
import unittest

from voynich.ciphers import (AnnealingDecryption, CipherKey, Ciphertext, Decryption,
                             Encryption, ReferenceDecryption, SubstitutionEncryption,
                             TextSource)
from voynich.decipher_search.core import Config, normalize


TRAINING = TextSource(("in principio erat verbum et verbum erat apud deum "
                       "aqua et terra et flores sunt in horto ") * 8,
                      ("latin",), "test:training")


class CipherApiTests(unittest.TestCase):
    def test_abstract_contracts_require_implementation(self):
        for interface in (Encryption, Decryption):
            with self.assertRaises(TypeError):
                interface()

    def test_round_trip_reference_and_explorer_matrix(self):
        solver = AnnealingDecryption(TRAINING, config=Config(steps=2, restarts=1))
        reference = ReferenceDecryption()
        examples = {"latin": ["Aqua est bona.", "Jūvat æquum!", "a"],
                    "italian": ["Nel mezzo del cammin.", "Perché è così?", "o"]}
        for language, texts in examples.items():
            for text in texts:
                for homophones in (1, 2):
                    for seed in (0, 17):
                        with self.subTest(language=language, text=text, homophones=homophones, seed=seed):
                            source = TextSource(text, (language,), "test:heldout")
                            fixture = SubstitutionEncryption(homophones=homophones).encrypt(
                                source, key_seed=seed, encryption_seed=seed + 1)
                            public = fixture.public_ciphertext()
                            for decoder in (reference, solver):
                                decoded = decoder.decrypt(public, key=fixture.key)
                                self.assertEqual(decoded.plaintext, normalize(text))
                                self.assertTrue(decoded.exact_coverage)

    def test_public_payload_does_not_contain_truth(self):
        fixture = SubstitutionEncryption().encrypt(TextSource("aqua", ("latin",), "source-secret"))
        self.assertEqual(set(asdict(fixture.public_ciphertext())), {"text", "cipher_id"})
        solver = AnnealingDecryption(TRAINING, config=Config(steps=1, restarts=1))
        with self.assertRaises(TypeError):
            solver.recover(fixture)

    def test_reproducible_separate_key_and_encryption_randomness(self):
        encryption = SubstitutionEncryption(homophones=2)
        source = TextSource("a" * 100, ("latin",), "test:repeat")
        first = encryption.encrypt(source, key_seed=3, encryption_seed=4)
        self.assertEqual(first, encryption.encrypt(source, key_seed=3, encryption_seed=4))
        second = encryption.encrypt(source, key_seed=3, encryption_seed=5)
        self.assertEqual(first.key, second.key)
        self.assertNotEqual(first.ciphertext, second.ciphertext)
        self.assertEqual({u for _, u in first.key.entries}, set("abcdefghijklmnopqrstuvwxyz"))

    def test_supplied_key_can_encrypt_another_passage(self):
        encryption = SubstitutionEncryption()
        fixture = encryption.encrypt(TextSource("aqua", ("latin",), "dev"))
        other = encryption.encrypt(TextSource("zebra", ("italian",), "reserved"), key=fixture.key)
        self.assertIsNone(other.key_seed)
        self.assertEqual(ReferenceDecryption().decrypt(other.ciphertext, key=fixture.key).plaintext, "zebra")

    def test_source_provenance_and_immutability(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.txt"
            path.write_text("Aqua è", encoding="utf-8")
            source = TextSource.from_file(path, languages=("latin", "italian"), source_id="work:1")
            self.assertEqual(source.text, "Aqua è")
            self.assertEqual(len(source.sha256), 64)
            self.assertEqual(source.uri, path.as_uri())
            fixture = SubstitutionEncryption().encrypt(source)
            self.assertEqual(fixture.plaintext.source, source)
            with self.assertRaises(FrozenInstanceError):
                source.text = "changed"

    def test_unknown_symbols_are_not_refitted(self):
        key = SubstitutionEncryption().generate_key(seed=1)
        partial = CipherKey(key.cipher_id, key.entries[:1])
        cipher = Ciphertext(key.entries[1][0], key.cipher_id)
        for decoder in (ReferenceDecryption(), AnnealingDecryption(TRAINING)):
            with self.assertRaises(ValueError):
                decoder.decrypt(cipher, key=partial)

    def test_recovery_adapter_returns_reproducible_ranked_candidates(self):
        fixture = SubstitutionEncryption().encrypt(TextSource("aqua est bona", ("latin",), "heldout"))
        config = Config(steps=15, restarts=2, keep=3, seed=3)
        solver = AnnealingDecryption(TRAINING, config=config)
        result = solver.recover(fixture.public_ciphertext())
        self.assertEqual(result, solver.recover(fixture.public_ciphertext()))
        self.assertEqual(result.evaluations, 32)
        self.assertGreater(len(result.candidates), 0)
        scores = [c.score for c in result.candidates]
        self.assertEqual(scores, sorted(scores))
        for candidate in result.candidates:
            self.assertEqual("".join(candidate.path), fixture.ciphertext.text)
            self.assertEqual(solver.decrypt(fixture.ciphertext, key=candidate.key).plaintext,
                             candidate.result.plaintext)
        self.assertEqual(result.training.source_id, "test:training")

    def test_unsupported_operations_fail_explicitly(self):
        with self.assertRaises(NotImplementedError):
            ReferenceDecryption().recover(Ciphertext("x", "unknown"))
        with self.assertRaises(NotImplementedError):
            AnnealingDecryption(TRAINING, config=Config(family="mixed"))
        with self.assertRaises(NotImplementedError):
            AnnealingDecryption(TRAINING, config=Config(spacing="infer"))
        with self.assertRaises(NotImplementedError):
            SubstitutionEncryption(homophones=3)
        with self.assertRaises(NotImplementedError):
            SubstitutionEncryption().prepare(TextSource("text", ("unknown",), "source"))

    def test_invalid_key_and_source(self):
        with self.assertRaises(ValueError):
            CipherKey("scheme", (("x", "a"), ("x", "b")))
        with self.assertRaises(ValueError):
            CipherKey("scheme", (("x", ""),))
        with self.assertRaises(ValueError):
            TextSource("text", (), "source")
        with self.assertRaises(ValueError):
            SubstitutionEncryption().prepare(TextSource("123?!", ("latin",), "source"))
        with self.assertRaises(ValueError):
            ReferenceDecryption().decrypt(Ciphertext("x", "other"), key=SubstitutionEncryption().generate_key(seed=1))

    def test_solver_rejects_spacing_that_would_be_silently_rewritten(self):
        solver = AnnealingDecryption(TRAINING)
        key = SubstitutionEncryption().generate_key(seed=1)
        with self.assertRaises(ValueError):
            solver.recover(Ciphertext("x  y", key.cipher_id))


if __name__ == "__main__":
    unittest.main()
