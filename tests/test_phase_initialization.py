import unittest

from voynich.laboratory.phase_report import lexical_links,pair_rows


class PhaseReportTests(unittest.TestCase):
    def test_word_agreement_requires_same_phase_and_cipher_word(self):
        row={'word_hits':{'pliny':{'distinct_hits':['esse']}},
             'candidate':{'key':{'a':'e','b':'s',chr(ord('a')+65536):'s',chr(ord('b')+65536):'e'}},
             'lines':['abba abba','baab']}
        links=lexical_links(row)
        self.assertEqual(links,{(0,'abba','esse'),(1,'baab','esse')})
        # Repeated occurrences of one mapping do not increase the hit count.
        self.assertEqual(len(links),2)

    def test_comparisons_do_not_pair_different_controls(self):
        rows=[{'case_id':case,'variant':variant} for case in ('original','shuffled')
              for variant in ('cold','separate-then-joint')]
        evidence={'rows':rows,'plan':{'case_ids':['original','shuffled']}}
        self.assertTrue(all(a['case_id']==b['case_id'] for a,b in pair_rows(evidence)))
        evidence['rows'].append(rows[0])
        with self.assertRaises(ValueError):pair_rows(evidence)


if __name__=='__main__':unittest.main()
