"""Measured known-key matrix and page-choice experiments on real corpora."""
import argparse
from collections import Counter
from dataclasses import asdict
import itertools
from pathlib import Path
import time

from voynich.ciphers.contracts import Document, Segment
from voynich.ciphers.pages import PageSubstitution, UniformPageChoices
from voynich.ciphers.units import UnitCipher
from voynich.decipher_search.core import LanguageModel, decode, digest
from voynich.laboratory.corpora import load_corpora
from voynich.laboratory.manifest import environment, file_hash
from voynich.paths import ROOT
from voynich.storage.artifacts import write_json


def method_matrix(training):
    pairs = [p for p, _ in Counter(training[i:i+2] for i in range(len(training)-1)
                                 if " " not in training[i:i+2]).most_common(4)]
    words = [w for w, _ in Counter(training.split()).most_common(30) if len(w) >= 3][:4]
    for family, homophones, spacing in itertools.product(("glyph", "groups", "mixed"), (1, 2),
                                                       ("preserve", "encoded")):
        for lengths in (("fixed",) if family == "glyph" else ("fixed", "variable")):
            units = () if family == "glyph" else tuple(pairs) if family == "groups" else tuple(dict.fromkeys(pairs + words))
            yield UnitCipher(family, homophones, lengths, spacing, units)


def run(output):
    started = time.monotonic()
    output.mkdir(parents=True, exist_ok=False)
    rows, examples, pages = [], [], []
    provenance = []
    for corpus in load_corpora():
        n = len(corpus.prepared)
        training = corpus.prepared[:int(.6*n)]
        model = LanguageModel(training)
        provenance.append({"id": corpus.id, "language": corpus.language, "work": corpus.work,
            "file_hash": file_hash(corpus.path), "raw_body_hash": corpus.raw_hash,
            "prepared_hash": digest(corpus.prepared), "normalization": corpus.normalization,
            "source_uri": corpus.source_uri, "prepared_length": n})
        for method in method_matrix(training):
            for seed, length in itertools.product((7, 19, 31, 43, 59), (120, 300, 600)):
                start = int(.65*n) + seed * 3
                plain = corpus.prepared[start:start+length].strip()
                key = method.generate_key(seed=seed)
                cipher, alignment = method.encrypt_text(plain, key, seed=seed+1)
                reference = method.decrypt_text(cipher, key)
                explorer = decode(cipher, key.as_mapping(), model, 8)
                reference_ok = reference.plaintexts == (plain,)
                explorer_ok = explorer.get("plaintext") == plain and explorer.get("valid")
                row = {"corpus": corpus.id, "language": corpus.language, "method": asdict(method),
                    "seed": seed, "requested_length": length, "actual_length": len(plain),
                    "cipher_length": len(cipher), "reference_exact": reference_ok,
                    "explorer_exact": bool(explorer_ok), "coverage": reference.coverage,
                    "plaintext_hash": digest(plain), "ciphertext_hash": digest(cipher),
                    "span": [start, start+length], "path_units": len(alignment)}
                rows.append(row)
                if seed == 7 and length == 300 and method.spacing == "preserve" and method.lengths == "fixed":
                    examples.append({**row, "plaintext": corpus.display(plain),
                        "storage_plaintext": plain, "ciphertext": cipher,
                        "reference_decoded": corpus.display(reference.plaintexts[0]),
                        "key": key.as_mapping()})
        for seed in (7,19,31,43,59):
            method = PageSubstitution()
            tables = method.generate_tables(seed=seed)
            p1, p2 = corpus.prepared[int(.7*n):int(.7*n)+180], corpus.prepared[int(.8*n):int(.8*n)+180]
            document = Document((Segment("p1", p1, 0,180), Segment("p2",p2,180,360)))
            choices = UniformPageChoices().sample(("p1","p2"), seed=seed)
            cipher = method.execute(document,tables,choices,decrypt=False)
            decoded = method.execute(cipher.document,tables,choices,decrypt=True)
            pages.append({"corpus":corpus.id,"seed":seed,"choices":choices,"exact":decoded.document==document})
    value = {"schema":1,"status":"completed","kind":"known-key-reversibility",
        "environment":environment(ROOT),"sources":provenance,"cases":rows,"examples":examples,
        "page_choices":pages,"elapsed_seconds":time.monotonic()-started,
        "summary":{"cases":len(rows),"reference_exact":sum(r["reference_exact"] for r in rows),
                   "explorer_exact":sum(r["explorer_exact"] for r in rows),
                   "page_cases":len(pages),"page_exact":sum(r["exact"] for r in pages)},
        "interpretation":"Known-key engineering evidence, not blind recovery or historical attestation."}
    write_json(output / "results.json",value)
    print(value["summary"])
    return value


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    run(parser.parse_args().output)
