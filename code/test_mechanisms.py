"""Tests for scientific invariants in the new mechanism benchmark."""
import importlib.util
import random
import unittest
from pathlib import Path

import mechanism_models as m

SPEC=importlib.util.spec_from_file_location('gate',Path(__file__).with_name('08_robustness_gate.py'))
g=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(g)


def line(words,number=1):
    return dict(page='f1r',folio='f1',locus=f'f1r.{number}',number=number,
                words=[dict(word=w or '?',clean=w is not None) for w in words],
                gaps=['ordinary']*(len(words)-1),meta={'L':'B'},paragraph_start=False,paragraph_end=False)


class MechanismTests(unittest.TestCase):
    def test_family_definition_groups_wrappers_and_runs(self):
        self.assertEqual(g.family('qokaii'),g.family('okai'))
        self.assertEqual(g.family('qokaii'),g.family('kai'))
        self.assertNotEqual(g.family('kai'),g.family('cho'))
        self.assertEqual(g.family('qo'),'<empty>')

    def test_glyph_modes_preserve_original_text(self):
        for mode in ('original','characters','minims'):
            self.assertEqual(''.join(g.glyphs('qocheeiin',mode)),'qocheeiin')

    def test_calibration_and_diagnostics_disjoint(self):
        self.assertFalse(set(m.CALIBRATION_SCALES)&set(m.DIAGNOSTICS))

    def test_encoder_roundtrip_for_all_retained_outputs(self):
        encoder=m.Encoder(m.ROOT/'data/mechanisms/naibbe_tables.csv')
        for unit,options in encoder.options.items():
            for word in options:self.assertEqual(encoder.decode([word]),unit)
        self.assertTrue(set('abcdefghijklmnopqrstuvwxyz'.replace('j','').replace('k','').replace('w',''))<=encoder.letters)

    def test_generators_repeat_and_preserve_plaintext(self):
        train=m.Training([line(['daiin','chol','or','qokar','chedy','al']*5)])
        encoder=m.Encoder(m.ROOT/'data/mechanisms/naibbe_tables.csv')
        for mechanism in m.CLASSES:
            config=dict(mechanism=mechanism,level=1,coupling=1)
            a,audit=m.generate(train,encoder,'loremipsumdolorsitamet'*100,100,config,123)
            b,_=m.generate(train,encoder,'loremipsumdolorsitamet'*100,100,config,123)
            self.assertEqual(a,b);self.assertEqual(len(a),100)
            if mechanism=='encoding':self.assertTrue(audit['roundtrip'])

    def test_unknown_slots_not_bridged(self):
        data=[line(['chol',None,'or'])]
        fp=m.fingerprint(data)
        self.assertEqual(fp['short_n']+fp['long_n'],0)
        self.assertEqual(fp['lag_n_1'],0)
        self.assertEqual(fp['lag_n_2'],0)
        replaced=m.apply_template(data,['daiin','qokar','al'])
        self.assertFalse(replaced[0]['words'][1]['clean'])

    def test_template_token_count_assertion(self):
        with self.assertRaises(AssertionError):m.apply_template([line(['or'])],['or','al'])

    def test_mutual_information_and_edit_sanity(self):
        self.assertAlmostEqual(m.mi([('a','x'),('b','y')]*10),1.)
        self.assertAlmostEqual(m.mi([('a','x'),('a','y'),('b','x'),('b','y')]*10),0.)
        self.assertEqual(m.edit_similarity('chol','chol'),1.)
        self.assertAlmostEqual(m.edit_similarity('chol','chor'),2/3)


if __name__=='__main__':unittest.main()
