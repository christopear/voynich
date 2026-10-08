from dataclasses import asdict
import itertools
from pathlib import Path
import tempfile
import unittest
from voynich.ciphers.ambiguity import enumerate_paths
from voynich.ciphers.contracts import Document, Segment
from voynich.ciphers.models import CipherKey, TextSource
from voynich.ciphers.pages import PageSubstitution, UniformPageChoices
from voynich.ciphers.units import UnitCipher
from voynich.decipher_search.core import LanguageModel, decode
from voynich.evaluation.scorers import PageEvaluator, independent_page_choices
from voynich.laboratory.fixtures import FixtureBuilder, SyntheticFixture, PublicInput
from voynich.search.strategies import PageChoiceSearch

LATIN = "in principio erat verbum et verbum erat apud deum "
ITALIAN = "nel mezzo del cammin di nostra vita mi ritrovai per una selva oscura "


class LaboratoryCipherTests(unittest.TestCase):
    def test_independent_roundtrip_matrix(self):
        cases = 0
        for language, sample in (("latin", LATIN), ("italian", ITALIAN)):
            for family, homophones, spacing, seed in itertools.product(
                    ("glyph", "groups", "mixed"), (1, 2), ("preserve", "encoded"), (0, 19)):
                for lengths in (("fixed",) if family == "glyph" else ("fixed", "variable")):
                    method = UnitCipher(family, homophones, lengths, spacing,
                        () if family == "glyph" else ("er",) if family == "groups" else ("er", "verbum", "vita"))
                    with self.subTest(language=language, method=method, seed=seed):
                        builder = FixtureBuilder(method)
                        source = TextSource(sample + " zyx j q ", (language,), "test")
                        fixture = builder.build(source, seed=seed)
                        self.assertEqual(fixture, builder.build(source, seed=seed))
                        reference = method.decrypt_text(fixture.public.ciphertext, fixture.truth.key)
                        explorer = decode(fixture.public.ciphertext, fixture.truth.key.as_mapping(),
                                          LanguageModel(sample * 5), 32)
                        self.assertEqual(reference.plaintexts, (fixture.truth.plaintext,))
                        self.assertEqual(explorer["plaintext"], fixture.truth.plaintext)
                        self.assertTrue(explorer["valid"])
                        self.assertEqual(set(asdict(fixture.public)), {"ciphertext", "method_id", "spacing", "role"})
                        for p0, p1, c0, c1 in fixture.truth.alignment:
                            code = fixture.public.ciphertext[c0:c1]
                            unit = " " if code == " " else fixture.truth.key.as_mapping()[code]
                            self.assertEqual(unit, fixture.truth.plaintext[p0:p1])
                        cases += 1
        self.assertEqual(cases, 80)

    def test_invalid_noninvertible_and_serialization(self):
        method = UnitCipher()
        key = method.generate_key(seed=0)
        self.assertEqual(method.decrypt_text("!", key).status, "no-valid-path")
        with self.assertRaises(ValueError):
            method.decrypt_text("", key)
        with self.assertRaises(ValueError):
            UnitCipher("groups", extra_units=("word",))
        grouped = UnitCipher("groups", lengths="variable")
        bad = CipherKey(grouped.method_id, tuple(("a" * (i + 1), u) for i, u in enumerate(grouped.units)))
        with self.assertRaises(ValueError):
            grouped.validate_key(bad)
        fixture = FixtureBuilder(method).build(TextSource(LATIN, ("latin",), "x"), seed=0)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "fixture"
            fixture.save(folder)
            self.assertEqual(SyntheticFixture.load_private(folder), fixture)
            self.assertEqual(PublicInput.load(folder / "public.json"), fixture.public)
            with self.assertRaises(FileExistsError):
                fixture.save(folder)
            public = (folder / "public.json").read_text()
            self.assertNotIn("key", public)
            self.assertNotIn("alignment", public)

    def test_six_table_choices_and_independence(self):
        method = PageSubstitution()
        tables = method.generate_tables(seed=4)
        plain = Document((Segment("p1", LATIN.strip(), 0, 50),
                          Segment("p2", LATIN.strip(), 50, 100)))
        policy = UniformPageChoices()
        choices = policy.sample(("p1", "p2"), seed=11)
        cipher = method.execute(plain, tables, choices, decrypt=False)
        restored = method.execute(cipher.document, tables, choices, decrypt=True)
        self.assertEqual(restored.document, plain)
        evaluator = PageEvaluator(cipher.document, tables, method, LATIN * 5)
        strategy = PageChoiceSearch(("p1", "p2"))
        candidates = strategy.propose(100)
        self.assertEqual(len(candidates), 36)
        ranked = sorted((evaluator(c).loss, c.data["choices"]) for c in candidates)
        independent = independent_page_choices(evaluator)
        self.assertEqual(evaluator(independent).loss, ranked[0][0])
        self.assertEqual(independent.data["choices"], list(choices))
        from dataclasses import replace
        with self.assertRaises(ValueError):
            independent_page_choices(replace(evaluator, method=PageSubstitution(coupled=True)))
        with self.assertRaises(ValueError):
            independent_page_choices(replace(evaluator, additive=False))
        coupled = PageSubstitution(coupled=True)
        encrypted = coupled.execute(plain, tables, choices, decrypt=False)
        self.assertEqual(coupled.execute(encrypted.document, tables, choices, decrypt=True).document, plain)

    def test_ambiguity_paths_vs_plaintexts_and_pruning(self):
        same = enumerate_paths("aa", (("a", "x", .5), ("aa", "xx", .25)))
        self.assertEqual(same.outcome.path_count, 2)
        self.assertEqual(same.outcome.status, "unique-plaintext")
        self.assertEqual(dict(same.masses), {"xx": .5})
        different = enumerate_paths("aa", (("a", "x", .5), ("aa", "y", .25)))
        self.assertEqual(different.outcome.status, "multiple-plaintexts")
        pruned = enumerate_paths("aa", (("a", "x", .5), ("aa", "y", .25)), max_paths=3)
        self.assertEqual(pruned.outcome.status, "unresolved")
        self.assertTrue(pruned.outcome.pruned)
        self.assertIn("not calibrated", pruned.mass_interpretation)

    def test_restricted_alphabets_roundtrip_and_serialize(self):
        from collections import Counter
        cases=0
        for size,lengths,homophones,spacing in itertools.product((12,20),('fixed','variable'),(1,2),('preserve','encoded')):
            method=UnitCipher('groups',homophones,lengths,spacing,('er','in'),alphabet='ABCDEFGHIJKLMNOPQRST'[:size])
            fixture=FixtureBuilder(method).build(TextSource(LATIN,('latin',),'test'),seed=7)
            reference=method.decrypt_text(fixture.public.ciphertext,fixture.truth.key)
            self.assertEqual(reference.plaintexts,(fixture.truth.plaintext,))
            explorer=decode(fixture.public.ciphertext,fixture.truth.key.as_mapping(),LanguageModel(LATIN*10),8)
            self.assertEqual(explorer['plaintext'],fixture.truth.plaintext)
            self.assertLessEqual(len(set(fixture.public.ciphertext)-{' '}),size)
            self.assertEqual(method.method_id,'prefix-unit-alphabet-v1')
            with tempfile.TemporaryDirectory() as directory:
                fixture.save(Path(directory)/'fixture')
                self.assertEqual(SyntheticFixture.load_private(Path(directory)/'fixture'),fixture)
            cases+=1
        self.assertEqual(cases,16)

    def test_default_key_generation_preserves_historical_replay(self):
        from voynich.laboratory.manifest import fingerprint
        methods=(UnitCipher(),UnitCipher('groups',2,'variable','encoded',('er','in')),
                 UnitCipher('mixed',1,'fixed','preserve',('er','herba')))
        hashes=('06dc0a7b7a01b9c47e03dda3471d2084193106a60f15f9c425b07700f132dd9d',
                '439258df528cc4ffe7e4aa1cd6abb433669643d83f4044caf11dc883d6143674',
                '6687e4dd4e3ab5477182d042a66faf1cb1741a2adc644b7ac58a416316b9a5f3')
        for method,expected in zip(methods,hashes):
            self.assertEqual(method.method_id,'prefix-unit-v1')
            self.assertEqual(fingerprint(method.generate_key(seed=7).as_mapping()),expected)
        with self.assertRaises(ValueError):UnitCipher(alphabet='aa')
        with self.assertRaises(ValueError):UnitCipher(alphabet='ab!')
        with self.assertRaises(ValueError):UnitCipher(alphabet='ABCDEFGHIJKLMNOPQRST').generate_key(seed=7)
