"""Post hoc descriptive rate tables for the v101 variant sets (not part of the pre-set rules)."""
import sys, importlib.util, json
from collections import Counter, defaultdict
sys.path.insert(0,'code')
spec=importlib.util.spec_from_file_location('vt','code/20_v101_variant_test.py'); vt=importlib.util.module_from_spec(spec); spec.loader.exec_module(vt)
import v101_data as vd
lines,mapping=vd.load_corpus(); coll=vd.represent(lines,mapping['collapse_table'])
def tab(rows, keyf, minor):
    c=defaultdict(Counter)
    for r in rows: c[keyf(r)][r['sym']]+=1
    out={}
    for k,v in sorted(c.items(), key=lambda kv:-sum(kv[1].values())):
        n=sum(v.values())
        if n>=20: out[str(k)]=(n, round(v[minor]/n,3))
    return out
res={}
for cls,members,minor in [('p',{'g','j'},'j'),('d',{'8','7','6'},'7'),('sh',set('235%+!#'),'2'),('r',set('yxYb'),'x'),('y',set('9('),'('),('k',set('hW'),'W'),('f',set('fu'),'u'),('cph',set('JG'),'G')]:
    rows=vt.occurrences(lines,coll,members)
    res[cls]={'minor':minor,
      'line_first_word': tab(rows, lambda r:(r['wi']==0), minor),
      'paragraph_first_line': tab(rows, lambda r:r['pfl'], minor),
      'glyph_pos': tab(rows, lambda r: vt.family_features(r,'POS','collapsed')['gpos'], minor),
      'next': tab(rows, lambda r: vt.ctx(r,'collapsed')[2], minor),
      'prev': tab(rows, lambda r: vt.ctx(r,'collapsed')[1], minor),
      'hand': tab(rows, lambda r:r['hand'], minor),
      'language': tab(rows, lambda r:r['lang'], minor)}
json.dump(res, open('results/v101_2026-09-26/variant_posthoc_rates.json','w'), indent=1, ensure_ascii=False)
for k in ('p','d','sh','f'):
    print(k, json.dumps(res[k], ensure_ascii=False))
