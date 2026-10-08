"""Ancient-family positive control: exhaustively recover an unknown shift."""
import argparse
from pathlib import Path
from voynich.ciphers.models import CipherKey
from voynich.ciphers.units import UnitCipher
from voynich.decipher_search.core import Config,digest
from voynich.evaluation.glyph import GlyphEvaluator
from voynich.evaluation.scorers import recovery_metrics
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.benchmark import control_input
from voynich.laboratory.corpora import load_corpora
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.manifest import DatasetRef,ExperimentSpec,environment,fingerprint
from voynich.paths import ROOT
from voynich.search.shifts import ShiftSearch,shift_key
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import write_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry

def run(output):
    output.mkdir(parents=True,exist_ok=False)
    env=environment(ROOT)
    engine=make_engine();registry=Registry(engine)
    rows=[]
    try:
        for source in load_corpora():
            n=len(source.prepared);a,b=int(.7*n),int(.82*n)
            training=source.prepared[:int(.6*n)]
            plain,frozen_plain=source.prepared[a:a+300],source.prepared[b:b+300]
            refs=tuple(DatasetRef(source.id+":prepared",source.language,digest(source.prepared),
                digest(text),role,start,end,source.normalization,source.work,source.source_uri)
                for role,start,end,text in (
                    ("training",0,int(.6*n),training),("development",a,a+300,plain),
                    ("evaluation",b,b+300,frozen_plain)))
            for shift in (3,11,23):
                method=UnitCipher()
                key=CipherKey(method.method_id,tuple(shift_key(shift).items()))
                cipher,_=method.encrypt_text(plain,key)
                frozen_cipher,_=method.encrypt_text(frozen_plain,key)
                public=PublicInput(cipher,method.method_id,"preserve")
                runs={}
                for control in ("positive","shuffled"):
                    request=control_input(public,control,shift)
                    strategy=ShiftSearch();scorer=GlyphEvaluator(request,training,Config())
                    spec=ExperimentSpec.create(family="caesar-shift",method_version="shift-26-v1",
                        datasets=refs,configuration={"execution_binding":fingerprint({
                            "strategy":strategy.identity(),"evaluator":scorer.identity(),"batch_size":13}),
                            "fixture_shift":shift,"control":control,
                            "historical_scope":"ancient shift family; modern 26-letter storage alphabet"},
                        environment=env,max_evaluations=27,seed=shift,retention={"top_k":2,"reservoir":1})
                    runs[control]=ExperimentRunner(registry,output/"runs").run(spec,strategy,scorer,batch_size=13)
                best=runs["positive"]["top"][0]
                recovered=best["candidate"]["shift"]
                frozen=GlyphEvaluator(PublicInput(frozen_cipher,method.method_id,"preserve","evaluation"),
                    training,Config())(Candidate.create("search-key-v1",key=best["candidate"]["key"]))
                rows.append({"corpus":source.id,"shift":shift,"recovered_shift":recovered,
                    "key_exact":shift==recovered,"development_exact":best["payload"]["plaintext"]==plain,
                    "frozen_exact":frozen.payload.get("plaintext")==frozen_plain,
                    "beats_shuffled":best["loss"]<runs["shuffled"]["top"][0]["loss"],
                    "evaluations":sum(r["evaluations"] for r in runs.values()),
                    "run_ids":{k:r["run_id"] for k,r in runs.items()}})
        value={"schema":1,"status":"completed","cases":rows,"environment":env,
               "summary":{"cases":len(rows),"key_exact":sum(r["key_exact"] for r in rows),
                    "frozen_exact":sum(r["frozen_exact"] for r in rows),
                    "beats_shuffled":sum(r["beats_shuffled"] for r in rows),
                    "evaluations":sum(r["evaluations"] for r in rows)}}
        write_json(output/"results.json",value)
        print(value["summary"])
    finally:
        engine.dispose()

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
    run(p.parse_args().output)
