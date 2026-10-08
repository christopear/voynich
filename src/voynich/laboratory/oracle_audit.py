"""Post-search diagnostics only: never expose fixture truth to an optimizer."""
import argparse
from dataclasses import asdict
from pathlib import Path

from voynich.decipher_search.core import Config, normalize
from voynich.evaluation.scorers import KeyEvaluator, recovery_metrics
from voynich.laboratory.fixtures import SyntheticFixture
from voynich.laboratory.manifest import file_hash
from voynich.paths import ROOT
from voynich.search.strategies import Candidate
from voynich.storage.artifacts import read_json, write_json


def classify_gap(accuracy, oracle_loss, selected_loss, reachable=True):
    if not reachable:
        return "representation-mismatch"
    if oracle_loss is None:
        return "oracle-invalid-under-objective"
    if accuracy >= .95:
        return "recovered-at-development-threshold"
    if selected_loss is None or oracle_loss < selected_loss - 1e-9:
        return "search-gap-demonstrated"
    return "objective-prefers-or-ties-found-wrong-answer"


def audit(directory):
    summary = read_json(directory / "summary.json")
    rows = []
    for case in summary["cases"]:
        folder = directory / "private-fixtures" / case["case"]
        fixture = SyntheticFixture.load_private(folder / "development")
        run = directory / "runs" / case["run_ids"]["positive"]
        manifest = read_json(run / "manifest.json")
        cfg = Config(**manifest["configuration"]["solver"])
        source = ROOT / "data" / fixture.truth.provenance["source_id"]
        if file_hash(source) != fixture.truth.provenance["raw_hash"]:
            raise ValueError("original source changed")
        raw = source.read_text()
        training = normalize(raw[:int(.6 * len(raw))])
        evaluator = KeyEvaluator(fixture.public, training, cfg)
        active = {fixture.public.ciphertext[a:b] for _, _, a, b in fixture.truth.alignment} - {" "}
        true_key = fixture.truth.key.as_mapping()
        full = evaluator(Candidate.create("search-key-v1", key=true_key))
        active_value = evaluator(Candidate.create("search-key-v1", key={c:true_key[c] for c in active}))
        selected_loss = case["losses"]["positive"]
        accuracy = (case["metrics"] or {}).get("nonspace_edit_accuracy",0)
        reachable = fixture.search_space(training, cfg)
        rows.append({"case":case["case"], "method":case["method"], "language":case["language"],
            "run_id":case["run_ids"]["positive"], "selected_loss":selected_loss,
            "development_accuracy":accuracy, "active_truth_loss":active_value.loss,
            "full_truth_loss":full.loss, "active_truth_score":asdict(active_value.score),
            "active_truth_exact":active_value.payload.get("plaintext")==fixture.truth.plaintext,
            "full_truth_exact":full.payload.get("plaintext")==fixture.truth.plaintext,
            "selected_minus_active_truth":None if selected_loss is None or active_value.loss is None else selected_loss-active_value.loss,
            "search_space":reachable,
            "diagnosis":classify_gap(accuracy,active_value.loss,selected_loss,reachable["in_search_space"])})
    return {"schema":1,"kind":"post-search-oracle-audit", "input_hash":file_hash(directory/"summary.json"),
        "cases":rows,"interpretation":"Active truth uses only codes occurring in development. Full truth additionally includes unused mappings and homophones. These are different codebook/choice costs; neither score was used during search. Search-gap evidence does not certify global optimality or rule out additional objective failures."}


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("input",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args();write_json(a.output,audit(a.input))
