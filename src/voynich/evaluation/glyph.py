"""Exact character-only specialization of the existing exploratory objective."""
from collections import Counter
from dataclasses import dataclass
import math
import string
from voynich.decipher_search.core import inventory, key_bits
from voynich.evaluation.outcomes import ScoreReport
from voynich.evaluation.scorers import KeyEvaluator, Evaluation, model


@dataclass(frozen=True)
class GlyphEvaluator(KeyEvaluator):
    def __post_init__(self):
        super().__post_init__()
        if self.config.family != "glyph" or self.config.spacing != "preserve":
            raise ValueError("fast evaluator is character-only with preserved spaces")

    def identity(self):
        return {**super().identity(), "evaluator":"exact-glyph-cost-v1"}

    def __call__(self,candidate):
        key=candidate.data["key"]
        cipher=self.public.ciphertext
        denominator=max(1,len(cipher.replace(" ","")))
        invalid=(not key or any(len(c)!=1 or c==" " or len(u)!=1 or u not in string.ascii_lowercase
                              for c,u in key.items()) or bool(set(cipher)-set(key)-{" "}))
        if invalid or not self.config.min_ratio <= 1 <= self.config.max_ratio:
            return Evaluation(ScoreReport("exact-glyph-cost-v1",(),denominator,0,False),{},"invalid")
        plain=cipher.translate(str.maketrans(key))
        lm=model(self.training,self.config.order)
        variants=Counter(key.values())
        counts=Counter(cipher.replace(" ",""))
        choices=sum(n*math.log2(variants[key[c]]) for c,n in counts.items())
        complexity=key_bits(key,len(inventory(lm,self.config)),len(set(cipher)-{" "}))
        score=ScoreReport("exact-glyph-cost-v1",(("language_bits",lm.nll(plain)),
            ("encoding_choice_bits",choices),("weighted_key_bits",self.config.key_weight*complexity)),denominator)
        return Evaluation(score,{"plaintext":plain,"path":list(cipher),
            "decoding":{"coverage":1,"uniqueness":"unique-under-this-key","algorithm":"direct-character",
                        "complete_enumeration":True}})
