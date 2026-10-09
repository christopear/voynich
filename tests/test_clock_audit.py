import unittest
from voynich.laboratory.clock_audit import paragraph_states,decode_states,common_mask


class ClockAuditTests(unittest.TestCase):
    def test_even_paragraph_length_is_not_identifiable(self):
        self.assertEqual(paragraph_states(10,[0,6]),[i%2 for i in range(10)])
        self.assertNotEqual(paragraph_states(16,[0,5,9]),[i%2 for i in range(16)])

    def test_reset_changes_state_without_changing_key(self):
        key={'a':'e',chr(ord('a')+65536):'i'}
        self.assertEqual(decode_states(['a']*4,[0,1,0,1],key)['plaintext'],'e i e i')
        self.assertEqual(decode_states(['a']*4,paragraph_states(4,[0,3]),key)['plaintext'],'e i e e')

    def test_comparison_uses_intersection_of_covered_words(self):
        a,b,n=common_mask('sanat ?? corpus','sa?at aqua corpus')
        self.assertEqual((a,b,n),('? ? corpus','? ? corpus',1))


if __name__=='__main__':unittest.main()
