"""Explicit opt-in benchmark. Planning validates files without encrypting or searching."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
import json
from pathlib import Path
import random
import statistics

from voynich.ciphers.models import TextSource
from voynich.ciphers.substitution import NORMALIZATION
from voynich.ciphers.units import UnitCipher
from voynich.decipher_search.core import Config, normalize, digest
from voynich.evaluation.scorers import KeyEvaluator, recovery_metrics
from voynich.experiments.runner import ExperimentRunner
from voynich.laboratory.fixtures import FixtureBuilder
from voynich.laboratory.manifest import (DatasetRef, ExperimentSpec, canonical, environment,
                                        fingerprint, stream_seed)
from voynich.paths import ROOT
from voynich.search.strategies import AnnealingSearch, Candidate
from voynich.storage.artifacts import read_json, write_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry

METHODS = {
    "glyph": UnitCipher(),
    "homophonic": UnitCipher(homophones=2),
    "groups": UnitCipher("groups", extra_units=("er", "in")),
    "mixed": UnitCipher("mixed", lengths="variable", extra_units=("er", "in", "verbum", "vita")),
}
CONTROLS = ("positive", "shuffled", "message-free", "mismatched")


def default_plan():
    return {"schema": 1, "source_hashes": {}, "sources": {"latin": "data/latin_alfonsi.txt", "italian": "data/italian_dante.txt"},
            "methods": list(METHODS), "seeds": [7, 19], "lengths": [120, 240],
            "controls": list(CONTROLS), "steps": 500, "restarts": 4, "beam": 8,
            "batch_size": 4, "top_k": 10, "reservoir": 10,
            "split": "raw-character spans: first 60% train; 5% gap; development; 5% gap; evaluation",
            "criteria": {"positive_nonspace_accuracy": .95, "frozen_nonspace_accuracy": .90,
                         "full_coverage_required": True,
                         "positive_loss_below_all_matched_negatives": True},
            "interpretation": "Engineering benchmark; same-work splits; no Voynich family exclusion."}


def validate_plan(plan, root=ROOT):
    if set(plan) != set(default_plan()) or plan["schema"] != 1:
        raise ValueError("unsupported or incomplete benchmark plan")
    for key in ("methods", "seeds", "lengths", "controls"):
        if not isinstance(plan[key], list) or not plan[key] or len(set(plan[key])) != len(plan[key]):
            raise ValueError(f"{key} must be a nonempty distinct list")
    if set(plan["methods"]) - METHODS.keys() or set(plan["controls"]) != set(CONTROLS):
        raise ValueError("unsupported methods or missing matched controls")
    if set(plan["sources"]) - {"latin", "italian"} or not plan["sources"]:
        raise ValueError("unsupported source languages")
    for key in ("steps", "restarts", "beam", "batch_size", "top_k", "reservoir"):
        if type(plan[key]) is not int or plan[key] < 1:
            raise ValueError(f"positive {key} required")
    if plan["batch_size"] > 1000:
        raise ValueError("batch size exceeds checkpoint limit")
    if any(type(x) is not int for x in plan["seeds"]):
        raise ValueError("integer seeds required")
    if any(type(x) is not int or x < 1 for x in plan["lengths"]):
        raise ValueError("positive passage lengths required")
    criteria = plan["criteria"]
    if set(criteria) != set(default_plan()["criteria"]):
        raise ValueError("unknown success criteria")
    for key in ("positive_nonspace_accuracy", "frozen_nonspace_accuracy"):
        if type(criteria[key]) not in (int, float) or not 0 <= criteria[key] <= 1:
            raise ValueError("accuracy thresholds must be 0..1")
    if criteria["full_coverage_required"] is not True or criteria["positive_loss_below_all_matched_negatives"] is not True:
        raise ValueError("initial gate requires coverage and matched negatives")
    # Interpretations/splits are fixed protocol identifiers, not editable prose.
    if plan["split"] != default_plan()["split"]:
        raise ValueError("unsupported split protocol")
    files = {}
    for language, name in plan["sources"].items():
        path = Path(name)
        path = path if path.is_absolute() else root / path
        text = path.read_text(encoding="utf-8")
        if len(normalize(text[:int(.6 * len(text))])) < 100:
            raise ValueError("training text too short")
        dev = int(.65 * len(text))
        evaluation = dev + max(plan["lengths"]) + max(50, int(.05 * len(text)))
        if evaluation + max(plan["lengths"]) > len(text):
            raise ValueError("source too short for disjoint maximum-length spans")
        files[language] = {"path": str(path.resolve()), "sha256": digest(text), "characters": len(text)}
    if plan["source_hashes"] and plan["source_hashes"] != {k: v["sha256"] for k, v in files.items()}:
        raise ValueError("source contents differ from the frozen plan")
    canonical(plan)
    count = len(files) * len(plan["methods"]) * len(plan["seeds"]) * len(plan["lengths"]) * len(CONTROLS)
    return {"schema": 1, "plan_id": fingerprint(plan), "files": files, "runs": count,
            "maximum_search_evaluations": count * plan["restarts"] * (plan["steps"] + 1),
            "execution_performed": False}


def control_input(public, kind, seed):
    if kind == "positive":
        return public
    rng = random.Random(seed)
    characters = list(public.ciphertext.replace(" ", ""))
    if kind == "shuffled":
        rng.shuffle(characters)
    elif kind == "message-free":
        counts = Counter(characters)
        characters = rng.choices(list(counts), weights=list(counts.values()), k=len(characters))
    elif kind == "mismatched":
        blocks = [characters[i:i+5] for i in range(0, len(characters), 5)]
        characters = [c for block in reversed(blocks) for c in block]
    else:
        raise ValueError("unknown control")
    iterator = iter(characters)
    return replace(public, ciphertext="".join(" " if c == " " else next(iterator) for c in public.ciphertext))


def run_benchmark(plan, output: Path, *, workers=1, root=ROOT, registry=None):
    """Never called by plan/preflight; starts real synthetic encryption and recovery."""
    preflight = validate_plan(plan, root)
    if not plan["source_hashes"]:
        raise ValueError("freeze source hashes before executing a benchmark")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "plan.json", plan)
    write_json(output / "preflight.json", preflight)
    env = environment(root)
    write_json(output / "environment.json", env)
    own_engine = make_engine() if registry is None else None
    registry = Registry(own_engine) if registry is None else registry
    results = []
    try:
        for language, source_info in preflight["files"].items():
            path = Path(source_info["path"])
            source = TextSource.from_file(path, languages=(language,), source_id=path.name)
            if source.sha256 != source_info["sha256"]:
                raise ValueError("source changed after preflight")
            training_stop = int(.6 * len(source.text))
            training = normalize(source.text[:training_stop])
            dev_start = int(.65 * len(source.text))
            eval_start = dev_start + max(plan["lengths"]) + max(50, int(.05 * len(source.text)))
            for name in plan["methods"]:
                method = METHODS[name]
                for seed in plan["seeds"]:
                    for length in plan["lengths"]:
                        case_id = f"{language}-{name}-{seed}-{length}"
                        builder = FixtureBuilder(method)
                        fixture = builder.build(source, seed=seed, start=dev_start, stop=dev_start + length)
                        heldout = builder.build(source, seed=seed, start=eval_start, stop=eval_start + length)
                        fixture.save(output / "private-fixtures" / case_id / "development")
                        heldout.save(output / "private-fixtures" / case_id / "evaluation")
                        refs = tuple(DatasetRef(source.source_id, language, source.sha256, digest(text),
                            role, start, stop, NORMALIZATION, source.source_id, source.uri) for role, start, stop, text in (
                                ("training", 0, training_stop, training),
                                ("development", dev_start, dev_start + length, fixture.truth.plaintext),
                                ("evaluation", eval_start, eval_start + length, heldout.truth.plaintext)))
                        cfg = Config(family=method.family, spacing="preserve", steps=plan["steps"],
                                     restarts=plan["restarts"], beam=plan["beam"], keep=plan["top_k"],
                                     seed=stream_seed(seed, case_id, "solver"))
                        selected = {}
                        # Finish all development selections before any truth metrics
                        # or reserved evaluation are exposed to the coordinator.
                        for control in plan["controls"]:
                            public = control_input(fixture.public, control, stream_seed(seed, case_id, control))
                            search, evaluator = AnnealingSearch(public, training, cfg), KeyEvaluator(public, training, cfg)
                            binding = fingerprint({"strategy": search.identity(), "evaluator": evaluator.identity(),
                                                   "batch_size": plan["batch_size"]})
                            spec = ExperimentSpec.create(family=method.family, method_version=method.method_id,
                                datasets=refs, configuration={"execution_binding": binding, "method": asdict(method),
                                    "solver": asdict(cfg), "control": control, "fixture_seed": seed,
                                    "case": case_id, "benchmark_plan": fingerprint(plan)},
                                environment=env, max_evaluations=cfg.restarts * (cfg.steps + 1), seed=seed,
                                retention={"top_k": plan["top_k"], "reservoir": plan["reservoir"]})
                            summary = ExperimentRunner(registry, output / "runs").run(
                                spec, search, evaluator, workers=workers, batch_size=plan["batch_size"])
                            selected[control] = summary
                        positive = selected["positive"]
                        best = positive["top"][0] if positive["top"] else None
                        frozen = None
                        metrics = None
                        if best:
                            prediction = best["payload"]["plaintext"]
                            key = best["candidate"]["key"]
                            metrics = recovery_metrics(prediction, fixture.truth.plaintext)
                            active_codes = {fixture.public.ciphertext[a:b] for _, _, a, b in fixture.truth.alignment} - {" "}
                            oracle = fixture.truth.key.as_mapping()
                            tokens = [fixture.public.ciphertext[a:b] for _, _, a, b in fixture.truth.alignment
                                      if fixture.public.ciphertext[a:b] != " "]
                            metrics["unit_token_accuracy"] = sum(key.get(c) == oracle[c] for c in tokens) / max(1, len(tokens))
                            metrics["development_coverage"] = best["score"]["coverage"]
                            metrics["active_key_accuracy"] = sum(key.get(code) == oracle[code] for code in active_codes) / max(1, len(active_codes))
                            frozen_eval = KeyEvaluator(replace(heldout.public, role="evaluation"), training, cfg)
                            frozen_value = frozen_eval(Candidate.create("search-key-v1", key=key))
                            frozen = {"coverage": frozen_value.score.coverage, "valid": frozen_value.score.valid,
                                      "metrics": recovery_metrics(frozen_value.payload.get("plaintext", ""), heldout.truth.plaintext)}
                        losses = {control: result["top"][0]["loss"] if result["top"] else None
                                  for control, result in selected.items()}
                        negatives = [losses[c] for c in CONTROLS if c != "positive"]
                        threshold = plan["criteria"]
                        passed = bool(best and metrics["nonspace_edit_accuracy"] >= threshold["positive_nonspace_accuracy"]
                            and frozen["valid"] and frozen["coverage"] == 1
                            and frozen["metrics"]["nonspace_edit_accuracy"] >= threshold["frozen_nonspace_accuracy"]
                            and all(x is not None and losses["positive"] < x for x in negatives))
                        item = {"case": case_id, "language": language, "method": name, "seed": seed,
                            "length": length, "search_space": fixture.search_space(training, cfg),
                            "run_ids": {k: v["run_id"] for k, v in selected.items()}, "losses": losses,
                            "metrics": metrics, "frozen": frozen, "engineering_gate_pass": passed,
                            "restart_diagnostics": {k: v["strategy_diagnostics"] for k, v in selected.items()},
                            "scientific_verdict": "not-assessed"}
                        results.append(item)
                        write_json(output / "cases" / f"{case_id}.json", item)
        aggregate = {}
        for name in plan["methods"]:
            rows = [r for r in results if r["method"] == name]
            accuracies = [r["metrics"]["nonspace_edit_accuracy"] for r in rows if r["metrics"]]
            aggregate[name] = {"cases": len(rows), "passed": sum(r["engineering_gate_pass"] for r in rows),
                "nonspace_mean": statistics.mean(accuracies) if accuracies else None,
                "nonspace_stdev_across_cases": statistics.stdev(accuracies) if len(accuracies) > 1 else None,
                "power_test_cases": sum(r["search_space"]["in_search_space"] for r in rows),
                "note": "Small descriptive sample, not an exclusion or calibrated probability."}
        write_json(output / "summary.json", {"schema": 1, "status": "completed",
                   "per_method": aggregate, "cases": results})
    except BaseException as exc:
        write_json(output / "failure.json", {"schema": 1, "status": "failed",
            "exception_type": type(exc).__name__, "completed_cases": len(results)})
        raise
    finally:
        if own_engine:
            own_engine.dispose()
    return aggregate


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan_cmd = sub.add_parser("plan", help="Write a predeclared plan without executing encryption/search")
    plan_cmd.add_argument("output", type=Path)
    check = sub.add_parser("preflight", help="Validate the plan and sources without executing encryption/search")
    check.add_argument("plan", type=Path)
    run = sub.add_parser("run", help="Explicitly execute the encryption/recovery benchmark")
    run.add_argument("plan", type=Path)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    if args.command == "plan":
        value = default_plan()
        report = validate_plan(value)
        value["source_hashes"] = {k: v["sha256"] for k, v in report["files"].items()}
        report = validate_plan(value)
        write_json(args.output, value)
        print(json.dumps(report, indent=2))
    elif args.command == "preflight":
        print(json.dumps(validate_plan(read_json(args.plan)), indent=2))
    else:
        if args.workers < 1:
            parser.error("--workers must be positive")
        print(json.dumps(run_benchmark(read_json(args.plan), args.output, workers=args.workers), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
