"""Exhaustive Caesar-family search over a declared modern 26-letter alphabet."""
import string
from voynich.search.strategies import Candidate

def shift_key(shift):
    if type(shift) is not int or not 0 <= shift < 26:
        raise ValueError("shift must be 0..25")
    alphabet=string.ascii_lowercase
    return {alphabet[(i+shift)%26]:letter for i,letter in enumerate(alphabet)}

class ShiftSearch:
    def __init__(self):
        self.cursor=0

    def identity(self):
        return {"strategy":"exhaustive-shifts-v1","alphabet":string.ascii_lowercase}

    def propose(self,limit):
        values=[Candidate.create("search-key-v1",key=shift_key(i),shift=i)
                for i in range(self.cursor,min(26,self.cursor+limit))]
        self.cursor+=len(values)
        return values

    def observe(self,results):
        pass

    def snapshot(self):
        return {"schema":1,"cursor":self.cursor,"strategy":"exhaustive-shifts-v1"}

    def restore(self,value):
        if value.get("schema")!=1 or value.get("strategy")!="exhaustive-shifts-v1" or not 0<=value["cursor"]<=26:
            raise ValueError("invalid shift checkpoint")
        self.cursor=value["cursor"]
