"""Post-result learner sensitivity: distinguish weak recovery from weak learner.

Chosen after seeing nearest-centroid recovery. Fixed random forest and 3-nearest
neighbours; no tuning, same withheld diagnostic inputs and grouped splits.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import mechanism_models as m

SPEC=importlib.util.spec_from_file_location('benchmark',Path(__file__).with_name('09_mechanism_benchmark.py'))
b=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(b)
OUT=b.OUT


def evaluate(rows,method):
    preds=[]
    for level in range(3):
        train=[r for r in rows if r['level']!=level];test=[r for r in rows if r['level']==level]
        model=(RandomForestClassifier(n_estimators=300,min_samples_leaf=2,max_features='sqrt',random_state=8221,n_jobs=1)
               if method=='forest' else make_pipeline(StandardScaler(),KNeighborsClassifier(n_neighbors=3)))
        model.fit(b.matrix(train),[r['mechanism'] for r in train])
        for row,pred in zip(test,model.predict(b.matrix(test))):preds.append(dict(truth=row['mechanism'],prediction=str(pred),level=level,seed=row['seed']))
    conf={c:{p:0 for p in m.CLASSES} for c in m.CLASSES}
    for p in preds:conf[p['truth']][p['prediction']]+=1
    return dict(accuracy=float(np.mean([p['truth']==p['prediction'] for p in preds])),n=len(preds),confusion=conf,predictions=preds)


def main():
    out={}
    for scale,path in [('evaluation','simulation_features.json'),('manuscript','large_simulation_features.json')]:
        rows=json.loads((OUT/path).read_text())
        out[scale]={method:evaluate(rows,method) for method in ('forest','knn3')}
    out['status']='Exploratory learner sensitivity selected after primary recovery results; no Voynich labels inferred.'
    out['code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (OUT/'recovery_sensitivity.json').write_text(json.dumps(out,indent=2))
    print({scale:{method:r['accuracy'] for method,r in values.items()} for scale,values in out.items() if isinstance(values,dict)})


if __name__=='__main__':main()
