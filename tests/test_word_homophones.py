import unittest
import numpy as np
from voynich.experiments.e28_word_homophones import make_key,encrypt,GRID,source_panels,new_slots,it_slots
from voynich.experiments.e27_unit_association import manuscript
from voynich.acquisition.unit_sources import sources

class WordHomophoneTests(unittest.TestCase):
 def test_disjoint_roundtrip_and_reproducibility(self):
  words=['aqua','mel','aqua','calida']*50
  for p in GRID:
   key,decoder=make_key(words,len(p));c=encrypt(words,key,p,101)
   self.assertEqual([decoder[t] for t in c],words)
   self.assertEqual(c,encrypt(words,key,p,101))
   self.assertEqual(len(decoder),len(set(words))*len(p))
 def test_population_information_identity(self):
  # Exact joint probabilities; both independent refinements and decoding preserve MI.
  joint=np.array([[.4,.1],[.1,.4]])
  def mi(j):
   denominator=j.sum(1)[:,None]*j.sum(0)[None,:];nz=j>0
   return float((j[nz]*np.log2(j[nz]/denominator[nz])).sum())
  for p in GRID:
   expanded=np.concatenate([joint[i:i+1]*q for i in range(2) for q in p],axis=0)
   self.assertAlmostEqual(mi(expanded),mi(joint))
 def test_reserved_chapters_and_folios_are_disjoint(self):
  for name,chapters in sources().items():
   if name not in ('cucina','celsus','pliny'):continue
   panels=source_panels(chapters)
   groups={s:{r['chapter'] for p in panels if p['split']==s for r in p['spans']} for s in ('development','validation')}
   self.assertFalse(groups['development'] & groups['validation'])
  old=manuscript()['split'];new=new_slots({r['folio'] for r in old})
  self.assertEqual(len(new),1024);self.assertEqual(len({r['folio'] for r in new}),16)
  self.assertFalse({r['folio'] for r in old}&{r['folio'] for r in new})
  for rows in (old,new):self.assertEqual(len(it_slots(rows)),1024)
