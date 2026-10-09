import unittest

import numpy as np

from voynich.acquisition.unit_sources import medical_chapters, recipe_chapters, sources
from voynich.cipher_families import encode, mi_codes
from voynich.experiments.e27_unit_association import (
    association, manuscript, page_tokens, source_panels, units,
)


class UnitAssociationTests(unittest.TestCase):
    def test_bijection_coarsening_and_state(self):
        a = encode(list('aabbbccccddddddd'))
        pages = encode([i//4 for i in range(16)])
        self.assertAlmostEqual(mi_codes(a, pages), mi_codes(encode([f'code-{v}' for v in a]), pages))
        self.assertLessEqual(mi_codes(a//2, pages), mi_codes(a, pages)+1e-12)
        source = np.zeros(16, dtype=int)
        self.assertEqual(mi_codes(source, pages), 0)
        self.assertGreater(mi_codes(pages, pages), 1)  # page-state coding violates fixed-channel premise

    def test_singletons_have_zero_excess(self):
        rows = [{'page': str(i//8), 'section': 'H'} for i in range(64)]
        result = association([str(i) for i in range(64)], rows, permutations=19)
        self.assertAlmostEqual(result['excess'], 0)
        self.assertGreater(result['raw'], 0)

    def test_segmentation_roundtrip_and_typed_mixture(self):
        words = ['aqua', 'et', 'medicina']
        for kind in ('letter', 'pair', 'syllable', 'word', 'mixed50'):
            stream = units(words, kind, {'aqua'})
            self.assertEqual(''.join(v.split(':')[1] for v in stream), ''.join(words))
        self.assertEqual(units(['a', 'aqua'], 'mixed50', {'a'}), ['w:a','l:a','l:q','l:u','l:a'])

    def test_extraction_excludes_editorial_material(self):
        xml = b'<root><div subtype="book" n="1"><div subtype="chapter" n="2"><head>BAD</head><p>aqua<note>BAD</note> calida <foreign>BAD</foreign> et mel</p></div></div></root>'
        self.assertEqual(medical_chapters(xml, {'1'})[0]['words'], ['aqua','calida','et','mel'])
        html = '<p>BAD</p><h2 class="break"><a name="IL"></a>BAD</h2><h3>BAD</h3><p class="center">BAD</p><p>Togli <span class="pagenum">BAD</span> aqua<a class="fnanchor">BAD</a> calda.</p><h2><a name="ANNOTAZIONI"></a></h2><p>BAD</p>'
        self.assertEqual(recipe_chapters(html)[0]['words'], ['togli','aqua','calda'])

    def test_manifest_sampling_and_dictionary_holdout(self):
        arms = manuscript()
        self.assertEqual(len(arms['split']), 1024)
        self.assertEqual(len({r['folio'] for r in arms['split']}), 16)
        self.assertEqual({r['page'] for r in arms['split']}, {r['page'] for r in arms['join']})
        for name, chapters in sources().items():
            panels = source_panels(chapters, 7)
            self.assertEqual(len(panels), 6)
            for panel in panels:
                self.assertEqual(len(panel['tokens']), 1024, name)
                self.assertFalse(set(panel['training_ids']) & {s['chapter'] for s in panel['spans']})
                self.assertEqual(len({s['chapter'] for s in panel['spans']}), 16)

    def test_uncertain_join_stops_at_hard_boundaries(self):
        line = dict(page='f1r', folio='f1', locus='f1r.1', meta={'L':'B','I':'H'},
                    paragraph_start=True, words=[{'word':w,'clean':True} for w in ['a','b','c','d']],
                    gaps=['uncertain','drawing','ordinary'])
        self.assertEqual([r['word'] for r in page_tokens([line], True)['f1r']], ['ab','c','d'])


if __name__ == '__main__':
    unittest.main()
