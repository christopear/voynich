from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
import json
import multiprocessing
import os
from pathlib import Path
import platform
import random
import subprocess
import time

from .core import (Config, LanguageModel, candidate_codes, decode, digest, edit_accuracy, evaluate,
                   inventory, normalize, prepare_cipher, search_restart, synthetic)


def read(path):
    return Path(path).read_text(encoding="utf-8")


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    os.replace(temp, path)


def provenance():
    from voynich.paths import ROOT
    root = ROOT
    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                         capture_output=True, text=True)
    files = [Path(__file__), Path(__file__).with_name("core.py")]
    return {"utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
            "git_head": rev.stdout.strip(), "implementation_sha256": {p.name: digest(read(p)) for p in files}}


def run_search(cipher, training, cfg, workers=1, checkpoint=None):
    started = time.monotonic()
    prepared = prepare_cipher(cipher, cfg.spacing)
    result = {"status": "running", "config": asdict(cfg), "provenance": provenance(),
              "cipher_sha256": digest(prepared), "normalized_training_sha256": digest(normalize(training)),
              "score_interpretation": "Exploratory best-path score plus description-length surrogate; not posterior evidence.",
              "runs": []}

    def record(run):
        result["runs"].append(run)
        result["runs"].sort(key=lambda x: x["restart"])
        result["elapsed_seconds"] = time.monotonic() - started
        if checkpoint:
            atomic_json(checkpoint, result)
        print(f"restart {run['restart'] + 1}/{cfg.restarts}: best={run['candidates'][0]['score']:.2f} bits", flush=True)

    if workers == 1:
        for restart in range(cfg.restarts):
            record(search_restart(cipher, training, cfg, restart))
    else:
        with ProcessPoolExecutor(max_workers=min(workers, cfg.restarts),
                                 mp_context=multiprocessing.get_context("spawn")) as pool:
            jobs = [pool.submit(search_restart, cipher, training, cfg, r) for r in range(cfg.restarts)]
            for future in as_completed(jobs):
                record(future.result())
    unique = {}
    for run in result["runs"]:
        for candidate in run["candidates"]:
            signature = tuple(sorted(candidate["key"].items()))
            unique[signature] = candidate
    result["candidates"] = sorted(unique.values(), key=lambda x: x["score"])[:cfg.keep]
    result["evaluations"] = sum(r["evaluations"] for r in result["runs"])
    # Agreement of independently optimized best keys; not a confidence interval.
    keys = [r["candidates"][0]["key"] for r in result["runs"]]
    result["restart_key_agreement"] = {
        c: max(sum(k.get(c) == u for k in keys) for u in {k.get(c) for k in keys}) / len(keys)
        for c in sorted(set(prepared) - {" "})}
    result["status"] = "complete"
    result["elapsed_seconds"] = time.monotonic() - started
    if checkpoint:
        atomic_json(checkpoint, result)
    return result


def frozen_evaluation(result, cipher, training, truth=None):
    cfg = Config(**result["config"])
    lm = LanguageModel(training, cfg.order)
    prepared = prepare_cipher(cipher, cfg.spacing)
    units = inventory(lm, cfg)
    rows = []
    for rank, candidate in enumerate(result["candidates"], 1):
        ev = evaluate(prepared, candidate["key"], lm, cfg, units)
        if truth is not None and ev["valid"]:
            ev["plaintext_edit_accuracy"] = edit_accuracy(ev["plaintext"], truth)
        rows.append({"development_rank": rank, **ev})
    return {"cipher_sha256": digest(prepared), "key_refitted": False,
            "selection": "development rank only; evaluation results must not select a new winner", "candidates": rows}


def split_fixture(source, family, seed, words, homophones, cfg=None):
    tokens = normalize(source).split()
    cutoff = int(len(tokens) * 0.7)
    gap = 50
    if len(tokens) - cutoff < 2 * words + gap:
        raise ValueError("source too short for 70% LM training, 50-word gap and two evaluation passages")
    training = " ".join(tokens[:cutoff])
    dev = " ".join(tokens[cutoff + gap:cutoff + gap + words])
    test = " ".join(tokens[cutoff + gap + words:cutoff + gap + 2 * words])
    allowed = inventory(LanguageModel(training, cfg.order), cfg) if cfg else None
    _, key, path = synthetic(dev + " " + test, family, seed, homophones, allowed)
    length = 0
    split = None
    for i, code in enumerate(path):
        length += 1 if code == " " else len(key[code])
        if length == len(dev):
            split = i + 1
            break
    if split is None or path[split] != " ":
        raise AssertionError("fixture split did not fall at a word boundary")
    return training, dev, test, "".join(path[:split]), "".join(path[split + 1:]), key


def negative_cipher(cipher, kind, seed):
    rng = random.Random(seed)
    letters = list(cipher.replace(" ", ""))
    if kind == "shuffled":
        rng.shuffle(letters)
    elif kind == "assembly":
        # Message-free iid symbols, preserving observed slot lengths.
        letters = rng.choices(letters, k=len(letters))
    elif kind == "mismatched":
        # A reversible block transposition outside the implemented decoder.
        letters = [c for i in range(0, len(letters), 7) for c in reversed(letters[i:i + 7])]
    else:
        return cipher
    iterator = iter(letters)
    return "".join(" " if c == " " else next(iterator) for c in cipher)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bounded Latin/Italian decipherment search; no automatic decipherment claims.")
    parser.add_argument("command", choices=["search", "controls"])
    parser.add_argument("--train", required=True, help="UTF-8 plaintext source; controls reserve the final 30 percent")
    parser.add_argument("--language", required=True, choices=["latin", "italian"], help="Provenance label, not automatic language detection")
    parser.add_argument("--cipher", help="Plain ASCII transcription, explicitly prepared outside this tool")
    parser.add_argument("--evaluation", help="Additional cipher passage; score frozen development keys only")
    parser.add_argument("--output", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--words", type=int, default=100, help="Words per synthetic development/evaluation passage")
    parser.add_argument("--homophones", type=int, choices=[1, 2], default=1)
    parser.add_argument("--control-kinds", nargs="+", choices=["positive", "shuffled", "assembly", "mismatched"],
                        default=["positive", "shuffled", "assembly", "mismatched"])
    parser.add_argument("--replicates", type=int, default=1)
    defaults = asdict(Config())
    for name, default in defaults.items():
        parser.add_argument("--" + name.replace("_", "-"), default=default, type=type(default))
    args = parser.parse_args(argv)
    cfg = Config(**{k: getattr(args, k) for k in defaults})
    cfg.validate()
    if min(args.workers, args.words, args.replicates) < 1:
        parser.error("workers, words and replicates must be positive")
    output = Path(args.output)
    checkpoint = output.with_suffix(output.suffix + ".checkpoint")
    if not args.overwrite and (output.exists() or checkpoint.exists()):
        parser.error("output/checkpoint exists; choose a new path or pass --overwrite")
    source = read(args.train)
    source_info = {"path": str(Path(args.train).resolve()), "sha256": digest(source),
                   "language": args.language, "normalization": "NFKD accent fold; ae/oe ligatures expanded; ASCII a-z; preserve i/j and u/v"}
    if args.command == "search":
        if not args.cipher:
            parser.error("search requires --cipher")
        result = run_search(read(args.cipher), source, cfg, args.workers, checkpoint)
        result["source"] = source_info
        result["cipher_path"] = str(Path(args.cipher).resolve())
        if args.evaluation:
            if digest(prepare_cipher(read(args.cipher), cfg.spacing)) == digest(prepare_cipher(read(args.evaluation), cfg.spacing)):
                parser.error("development and evaluation ciphertext are identical")
            result["evaluation"] = frozen_evaluation(result, read(args.evaluation), source)
        atomic_json(output, result)
    else:
        if args.cipher or args.evaluation:
            parser.error("controls generates its own development/evaluation ciphertext")
        if cfg.spacing != "preserve":
            parser.error("initial synthetic recovery controls require --spacing preserve; infer mode needs separate calibration")
        report = {"status": "running", "source": source_info, "config": asdict(cfg),
                  "provenance": provenance(), "split": "first 70% words train LM; 50-word gap; disjoint development/evaluation passages",
                  "interpretation": "Engineering calibration; no pass threshold or Voynich conclusion. A single replicate cannot calibrate false discovery.",
                  "cases": []}
        for replicate in range(args.replicates):
            training, truth, test_truth, cipher, test_cipher, key = split_fixture(
                source, cfg.family, cfg.seed + replicate, args.words, args.homophones, cfg)
            oracle = decode(cipher, key, LanguageModel(training, cfg.order), cfg.beam)
            if not oracle["valid"] or oracle["plaintext"] != truth:
                raise AssertionError("known-key positive fixture must decode exactly")
            for kind in dict.fromkeys(args.control_kinds):
                dev = negative_cipher(cipher, kind, cfg.seed + replicate + 17)
                test = negative_cipher(test_cipher, kind, cfg.seed + replicate + 29)
                # Same search budget and seed for each control kind.
                case = run_search(dev, training, cfg, args.workers, checkpoint)
                case.update(kind=kind, replicate=replicate, development_cipher=dev,
                            evaluation_cipher=test, truth_plaintext=truth if kind in {"positive", "mismatched"} else None)
                if kind == "positive":
                    case["oracle_key"] = key
                    case["oracle_exact_recovery"] = True
                    eligible = set(candidate_codes(dev, cfg)) | (set(dev) - {" "})
                    development_codes = {c for c in key if c in dev}
                    outside = sorted(development_codes - eligible)
                    too_many = sum(len(c) > 1 for c in development_codes) > cfg.extra_codes
                    case["truth_search_space_check"] = {
                        "oracle_codes_outside_candidate_inventory": outside,
                        "oracle_exceeds_extra_code_limit": too_many,
                        "oracle_embedding_supported": not outside and not too_many,
                        "note": "Conservative substring check; a different equivalent key may exist. Failure prevents interpreting nonrecovery as optimizer failure alone."}
                    for candidate in case["candidates"]:
                        candidate["plaintext_edit_accuracy"] = edit_accuracy(candidate["plaintext"], truth)
                case["evaluation"] = frozen_evaluation(case, test, training,
                                                       test_truth if kind in {"positive", "mismatched"} else None)
                report["cases"].append(case)
                atomic_json(output, report)
        report["status"] = "complete"
        atomic_json(output, report)
    print(f"Saved {output}", flush=True)


if __name__ == "__main__":
    main()
