"""Exact recovery of unknown page choices with six known tables."""
import argparse
from dataclasses import asdict
from pathlib import Path
from voynich.ciphers.contracts import Document, Segment
from voynich.ciphers.pages import PageSubstitution, UniformPageChoices
from voynich.decipher_search.core import digest
from voynich.evaluation.scorers import PageEvaluator, independent_page_choices
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.corpora import load_corpora
from voynich.laboratory.manifest import DatasetRef, ExperimentSpec, environment, fingerprint
from voynich.paths import ROOT
from voynich.search.strategies import PageChoiceSearch
from voynich.storage.artifacts import write_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry

def run(output):
    output.mkdir(parents=True,exist_ok=False)
    env=environment(ROOT)
    engine=make_engine()
    registry=Registry(engine)
    cases=[]
    try:
        for source in load_corpora():
            n=len(source.prepared)
            training=source.prepared[:int(.6*n)]
            a,b=int(.7*n),int(.8*n)
            plain=Document((Segment("p1",source.prepared[a:a+180],a,a+180),
                            Segment("p2",source.prepared[b:b+180],b,b+180)))
            for coupled in (False,True):
                method=PageSubstitution(coupled=coupled)
                for seed in (7,19,31,43,59):
                    tables=method.generate_tables(seed=seed)
                    truth_choices=UniformPageChoices().sample(("p1","p2"),seed=seed)
                    encrypted=method.execute(plain,tables,truth_choices,decrypt=False)
                    evaluator=PageEvaluator(encrypted.document,tables,method,training)
                    search=PageChoiceSearch(("p1","p2"))
                    refs=tuple(DatasetRef(source.id+":prepared",source.language,digest(source.prepared),
                        digest(text),role,start,stop,source.normalization,source.work,source.source_uri)
                        for role,start,stop,text in (
                        ("training",0,int(.6*n),training),
                        ("development",a,a+180,plain.pages[0].text),
                        ("development",b,b+180,plain.pages[1].text)))
                    spec=ExperimentSpec.create(family="page-choice-known-tables",method_version="page-substitution-v1",
                        datasets=refs,configuration={"execution_binding":fingerprint({
                            "strategy":search.identity(),"evaluator":evaluator.identity(),"batch_size":12}),
                            "scope":"tables known; only page choices unknown","coupled":coupled,"seed":seed},
                        environment=env,max_evaluations=37,seed=seed,retention={"top_k":2,"reservoir":1})
                    result=ExperimentRunner(registry,output/"runs").run(spec,search,evaluator,batch_size=12)
                    best=result["top"][0]
                    predicted=tuple(best["candidate"]["choices"])
                    shortcut=None
                    if not coupled:
                        shortcut=independent_page_choices(evaluator).data["choices"]
                    cases.append({"corpus":source.id,"seed":seed,"coupled":coupled,"truth":truth_choices,
                        "predicted":predicted,"choices_exact":predicted==truth_choices,
                        "plaintext_exact":best["payload"]["plaintexts"]==[p.text for p in plain.pages],
                        "shortcut_matches":tuple(shortcut)==predicted if shortcut is not None else None,
                        "evaluations":result["evaluations"],"run_id":result["run_id"],
                        "loss_margin":result["top"][1]["loss"]-best["loss"]})
        value={"schema":1,"status":"completed","cases":cases,"environment":env,
            "summary":{"cases":len(cases),"choices_exact":sum(c["choices_exact"] for c in cases),
                "plaintext_exact":sum(c["plaintext_exact"] for c in cases),
                "evaluations":sum(c["evaluations"] for c in cases)},
            "interpretation":"Known tables, unknown page choices; not arbitrary unknown-key recovery."}
        write_json(output/"results.json",value)
        print(value["summary"])
    finally:
        engine.dispose()

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
    run(p.parse_args().output)
