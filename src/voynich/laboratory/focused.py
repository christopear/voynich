"""Predeclared follow-up: longer text, injective search and matched controls."""
import argparse
from dataclasses import asdict, replace
from pathlib import Path
import time
from voynich.ciphers.units import UnitCipher
from voynich.decipher_search.core import Config, digest
from voynich.evaluation.glyph import GlyphEvaluator
from voynich.evaluation.scorers import recovery_metrics
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.benchmark import CONTROLS, control_input
from voynich.laboratory.corpora import load_corpora
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.manifest import DatasetRef, ExperimentSpec, environment, fingerprint, file_hash
from voynich.paths import ROOT
from voynich.search.monoalphabetic import MonoalphabeticSearch
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import write_json, read_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry


def plan():
    return {"schema":1,"corpora":["alfonsi","dante","caesar","homer"],"seeds":[7],
            "length":600,"steps":4000,"restarts":4,"order":4,
            "strategy":"injective-annealing-v1","scorer":"exact-glyph-cost-v1",
            "criteria":{"development":.95,"frozen":.9,"full_coverage":True,"beat_all_controls":True},
            "scope":"Exploratory follow-up changes length, budget and search constraints together; not an isolated ablation."}


def run(protocol,output):
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/"plan.json",protocol)
    env=environment(ROOT)
    write_json(output/"environment.json",env)
    engine=make_engine()
    registry=Registry(engine)
    results=[]
    started=time.monotonic()
    try:
        for corpus in load_corpora():
            if corpus.id not in protocol["corpora"]:
                continue
            n=len(corpus.prepared)
            training=corpus.prepared[:int(.6*n)]
            start, frozen_start=int(.68*n),int(.82*n)
            plain=corpus.prepared[start:start+protocol["length"]].strip()
            frozen_plain=corpus.prepared[frozen_start:frozen_start+protocol["length"]].strip()
            refs=tuple(DatasetRef(corpus.id+":prepared",corpus.language,digest(corpus.prepared),
                digest(text),role,a,b,corpus.normalization,corpus.work,corpus.source_uri)
                for role,a,b,text in (("training",0,int(.6*n),training),
                    ("development",start,start+len(plain),plain),
                    ("evaluation",frozen_start,frozen_start+len(frozen_plain),frozen_plain)))
            for seed in protocol["seeds"]:
                method=UnitCipher()
                key=method.generate_key(seed=seed)
                cipher,_=method.encrypt_text(plain,key,seed=seed+1)
                frozen_cipher,_=method.encrypt_text(frozen_plain,key,seed=seed+2)
                public=PublicInput(cipher,method.method_id,"preserve")
                selected={}
                cfg=Config(steps=protocol["steps"],restarts=protocol["restarts"],order=protocol["order"],seed=seed)
                for control in CONTROLS:
                    request=control_input(public,control,seed)
                    search=MonoalphabeticSearch(request,training,cfg)
                    evaluator=GlyphEvaluator(request,training,cfg)
                    binding=fingerprint({"strategy":search.identity(),"evaluator":evaluator.identity(),"batch_size":4})
                    spec=ExperimentSpec.create(family="monoalphabetic-injective",
                        method_version=method.method_id,datasets=refs,
                        configuration={"execution_binding":binding,"protocol":protocol,"corpus":corpus.id,
                            "source_file_hash":file_hash(corpus.path),"offset_space":"prepared source characters",
                            "control":control,"fixture_seed":seed,"solver":asdict(cfg)},
                        environment=env,max_evaluations=cfg.restarts*(cfg.steps+1),seed=seed,
                        retention={"top_k":3,"reservoir":3})
                    print(corpus.id,seed,control,flush=True)
                    selected[control]=ExperimentRunner(registry,output/"runs").run(spec,search,evaluator,batch_size=4,workers=1)
                best=selected["positive"]["top"][0]
                candidate=Candidate.create("search-key-v1",key=best["candidate"]["key"])
                frozen=GlyphEvaluator(PublicInput(frozen_cipher,method.method_id,"preserve","evaluation"),training,cfg)(candidate)
                metrics=recovery_metrics(best["payload"]["plaintext"],plain)
                frozen_metrics=recovery_metrics(frozen.payload.get("plaintext",""),frozen_plain)
                losses={kind: result["top"][0]["loss"] if result["top"] else None for kind,result in selected.items()}
                gate=bool(metrics["nonspace_edit_accuracy"]>=protocol["criteria"]["development"] and
                    frozen_metrics["nonspace_edit_accuracy"]>=protocol["criteria"]["frozen"] and
                    frozen.score.coverage==1 and all(losses[c] is not None and losses["positive"]<losses[c]
                                                  for c in CONTROLS if c!="positive"))
                item={"corpus":corpus.id,"language":corpus.language,"seed":seed,"length":len(plain),
                    "metrics":metrics,"frozen_metrics":frozen_metrics,"frozen_coverage":frozen.score.coverage,
                    "losses":losses,"gate_pass":gate,
                    "run_ids":{c:r["run_id"] for c,r in selected.items()},
                    "evaluations":sum(r["evaluations"] for r in selected.values()),
                    "examples":{"plaintext":corpus.display(plain),"ciphertext":cipher,
                        "recovered_storage":best["payload"]["plaintext"],"storage_truth":plain,
                        "frozen_storage":frozen.payload.get("plaintext",""),"frozen_truth":frozen_plain},
                    "interpretation":"Exploratory follow-up; one key per source, not calibrated family power."}
                results.append(item)
                write_json(output/"cases"/f"{corpus.id}-{seed}.json",item)
        value={"schema":1,"status":"completed","cases":results,"plan":protocol,
               "elapsed_seconds":time.monotonic()-started}
        write_json(output/"summary.json",value)
        print([(x["corpus"],x["metrics"]["nonspace_edit_accuracy"],x["gate_pass"]) for x in results],flush=True)
    finally:
        engine.dispose()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--plan",type=Path,required=True)
    args=parser.parse_args()
    run(read_json(args.plan),args.output)
