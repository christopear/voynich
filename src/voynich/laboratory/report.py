"""Export an auditable, self-contained operating report from completed studies."""
import argparse
from collections import defaultdict
import html
from pathlib import Path
import statistics
from voynich.laboratory.manifest import file_hash, fingerprint
from voynich.storage.artifacts import read_json, write_json

def percent(value):
    return "—" if value is None else f"{value:.1%}"

def compile_evidence(roundtrips, baseline, focused, pages, shifts, ablations=()):
    matrix=read_json(roundtrips/"results.json")
    initial=read_json(baseline/"summary.json")
    follow=read_json(focused/"summary.json")
    page_results=read_json(pages/"results.json")
    shift_results=read_json(shifts/"results.json")
    if any(d["status"]!="completed" for d in (matrix,initial,follow,page_results,shift_results)):
        raise ValueError("final report requires completed studies")
    # Post-search diagnostics only: these values never enter proposal or selection.
    for case in initial["cases"]:
        folder=baseline/"private-fixtures"/case["case"]
        public=read_json(folder/"development"/"public.json")
        heldout=read_json(folder/"evaluation"/"public.json")
        truth=read_json(folder/"development"/"truth.json")
        frozen_truth=read_json(folder/"evaluation"/"truth.json")
        used={public["ciphertext"][a:b] for _,_,a,b in truth["alignment"]}-{ " " }
        reserved={heldout["ciphertext"][a:b] for _,_,a,b in frozen_truth["alignment"]}-{ " " }
        reasons=[]
        if case["metrics"] is None or case["metrics"]["nonspace_edit_accuracy"]<.95:
            reasons.append("development accuracy below gate")
        if not case["frozen"] or not case["frozen"]["valid"]:
            reasons.append("no complete frozen decode")
        elif case["frozen"]["metrics"]["nonspace_edit_accuracy"]<.9:
            reasons.append("frozen accuracy below gate")
        loss=case["losses"].get("positive")
        if loss is None or any(v is None or loss>=v for k,v in case["losses"].items() if k!="positive"):
            reasons.append("does not beat every matched control")
        case["posthoc_diagnostics"]={"unseen_frozen_true_codes":len(reserved-used),
            "new_frozen_cipher_characters":len(set(heldout["ciphertext"])-set(public["ciphertext"])),
            "gate_failure_reasons":reasons,
            "scope":"Oracle-based post-search diagnostic, never supplied to the solver."}
    ablation_results=[{"directory":str(path),"results":read_json(path/"summary.json")} for path in ablations]
    if any(item["results"]["status"]!="completed" for item in ablation_results):
        raise ValueError("ablation is incomplete")
    runs=[]
    environments={}
    for directory in (baseline,focused,pages,shifts,*ablations):
        for path in sorted(directory.glob("runs/*/summary.json")):
            result=read_json(path)
            manifest=read_json(path.parent/"manifest.json")
            env=manifest.pop("environment")
            env_id=fingerprint(env)
            environments[env_id]=env
            runs.append({"run_id":result["run_id"],"spec_id":result["spec_id"],
                "manifest":{**manifest,"environment_id":env_id},
                "state":result["state"],"stop_reason":result["stop_reason"],
                "evaluations":result["evaluations"],"failures":result["failures"],
                "best":result["top"][:1],"summary_sha256":file_hash(path),
                "local_artifacts":str(path.parent),
                "export_retention":"one winner; full bounded retention remains in local artifacts"})
    return {"schema":1,"roundtrips":matrix,"baseline":initial,"focused":follow,
        "runs":runs,"environments":environments,"page_recovery":page_results,"shift_recovery":shift_results,
        "ablations":ablation_results,
        "total_search_evaluations":sum(r["evaluations"] for r in runs),
        "execution_errors":sum(r["failures"] for r in runs),
        "interpretation":"Synthetic engineering evidence; no Voynich ciphertext tested."}

def table(headers, rows, id=None):
    ident=f' id="{id}"' if id else ""
    return f'<div class="scroll"><table{ident}><thead><tr>'+''.join(
        f'<th>{html.escape(str(h))}</th>' for h in headers)+'</tr></thead><tbody>'+''.join(
        '<tr>'+''.join(f'<td>{html.escape(str(c))}</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'

def comparison(title, plain, recovered, cipher="", note=""):
    esc=html.escape
    return f"""<details><summary>{esc(title)}</summary><p>{esc(note)}</p>
    <div class="compare"><div><h4>Prepared truth</h4><pre>{esc(plain)}</pre></div>
    <div><h4>Decoded text</h4><pre>{esc(recovered) or 'No complete decode: uncovered symbols/invalid path.'}</pre></div></div>
    <h4>Ciphertext</h4><pre>{esc(cipher)}</pre></details>"""

def build_report(evidence, output):
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/"evidence.json",evidence)
    matrix=evidence["roundtrips"]
    initial=evidence["baseline"]["cases"]
    focused=evidence["focused"]["cases"]
    groups=defaultdict(list)
    for row in matrix["cases"]:
        groups[row["corpus"]].append(row)
    page_summary=evidence["page_recovery"]["summary"]
    shift_summary=evidence["shift_recovery"]["summary"]
    finite_table=table(["Finite recovery task","Cases","Recovered exactly","Frozen transfer","Scope"],[
        ["Caesar-family shift",shift_summary["cases"],shift_summary["key_exact"],shift_summary["frozen_exact"],
         "unknown shift; 26 candidates; every positive beats shuffled control"],
        ["Page choices",page_summary["cases"],page_summary["choices_exact"],"not a transfer experiment",
         "six known tables; 36 choice paths; independent/coupled state"]])
    sources=table(["Work","Language","Reference exact","Explorer exact","Preparation"],[
        [s["work"],s["language"],f'{sum(r["reference_exact"] for r in groups[s["id"]])}/{len(groups[s["id"]])}',
         f'{sum(r["explorer_exact"] for r in groups[s["id"]])}/{len(groups[s["id"]])}',s["normalization"]]
        for s in matrix["sources"]])
    initial_rows=[]
    for row in initial:
        metrics=row["metrics"] or {}
        frozen=row["frozen"] or {}
        initial_rows.append([row["case"],percent(metrics.get("nonspace_edit_accuracy")),
            percent((frozen.get("metrics") or {}).get("nonspace_edit_accuracy")),
            percent(frozen.get("coverage")),row.get("posthoc_diagnostics",{}).get("unseen_frozen_true_codes","—"),"within active inventory" if row["search_space"]["in_search_space"] else "challenge",
            "PASS" if row["engineering_gate_pass"] else "FAIL"])
    baseline_table=table(["Case","Development","Frozen","Coverage","Unseen true codes","Search space","Gate"],initial_rows,"initial")
    focus_table=table(["Source","Language","Development","Frozen","Frozen coverage","Gate"],[
        [r["corpus"],r["language"],percent(r["metrics"]["nonspace_edit_accuracy"]),
         percent(r["frozen_metrics"]["nonspace_edit_accuracy"]),percent(r["frozen_coverage"]),
         "PASS" if r["gate_pass"] else "FAIL"] for r in focused])
    examples="".join(comparison(
        f'{r["corpus"]} / {r["method"]["family"]} / {r["method"]["homophones"]} homophone(s)',
        r["plaintext"],r["reference_decoded"],r["ciphertext"]) for r in matrix["examples"])
    recovered=""
    for row in focused:
        ex=row["examples"]
        losses=" · ".join(f"{k}: {v:.3f}" if v is not None else f"{k}: invalid" for k,v in row["losses"].items())
        recovered+=comparison(row["corpus"]+" — blind recovery",ex["storage_truth"],ex["recovered_storage"],
            ex["ciphertext"],losses+" exploratory bits/input symbol; lower is better within this case.")
        recovered+=comparison(row["corpus"]+" — frozen-key transfer",ex["frozen_truth"],ex["frozen_storage"])
    means=defaultdict(list)
    for row in initial:
        if row["metrics"]:
            means[row["method"]].append(row["metrics"]["nonspace_edit_accuracy"])
    means_table=table(["Method","Mean development non-space accuracy","Cases"],[
        [k,percent(statistics.mean(v)),len(v)] for k,v in means.items()])
    ablation_rows=[]
    for group in evidence.get("ablations",[]):
        for row in group["results"]["cases"]:
            protocol=group["results"]["plan"]
            ablation_rows.append([row["corpus"],protocol["length"],protocol["steps"],
                "generic",percent(row["metrics"]["nonspace_edit_accuracy"]),
                percent(row["frozen_metrics"]["nonspace_edit_accuracy"])])
    for row in focused:
        if row["corpus"] in {"alfonsi","dante"}:
            ablation_rows.append([row["corpus"],600,4000,"injective",
                percent(row["metrics"]["nonspace_edit_accuracy"]),percent(row["frozen_metrics"]["nonspace_edit_accuracy"])])
    ablation_table=table(["Work","Prepared length","Steps/chain","Proposals","Development","Frozen"],
                        sorted(ablation_rows,key=lambda r:(r[0],r[1],r[2],r[3])))
    content=f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Cipher laboratory — operating report</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{color-scheme:light;--ink:#142b35;--line:#cedbdc;--accent:#126b69}}
*{{box-sizing:border-box}}body{{margin:0;background:#edf3f2;color:var(--ink);font:16px/1.6 system-ui,sans-serif}}
main{{max-width:1240px;margin:auto;padding:48px 32px}}h1{{font-size:42px;line-height:1.15;margin:12px 0 24px}}h2{{margin-top:42px;font-size:27px}}
p{{max-width:100ch}}a{{color:var(--accent)}}.kicker{{text-transform:uppercase;letter-spacing:.13em;font-weight:650;color:var(--accent);font-size:13px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:28px 0}}.card{{background:white;border:1px solid var(--line);padding:20px;border-radius:12px}}
.number{{display:block;font-size:32px;font-weight:720}}.note{{background:#fff8df;padding:18px 22px;border-left:4px solid #af7b19}}
table{{border-collapse:collapse;width:100%;background:white;font-size:14px}}th,td{{padding:12px 14px;text-align:left;border-bottom:1px solid var(--line)}}
th{{background:#dceae8}}.scroll{{overflow:auto}}details{{background:white;border:1px solid var(--line);border-radius:8px;margin:12px 0;padding:14px 18px}}
summary{{cursor:pointer;font-weight:650}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#eff4f5;padding:16px;font-size:14px;line-height:1.7}}
.compare{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}input{{width:100%;padding:12px;border:1px solid var(--line);border-radius:6px;margin:12px 0}}
footer{{margin-top:45px;border-top:1px solid var(--line);padding-top:20px;color:#48606b;font-size:13px}}
@media(max-width:750px){{main{{padding:24px 16px}}h1{{font-size:32px}}.cards{{grid-template-columns:1fr 1fr}}.compare{{grid-template-columns:1fr}}}}
@media print{{body{{background:white}}main{{padding:0}}input{{display:none}}}}
</style><main><div class="kicker">Voynich research laboratory · operating evidence · 8 October 2026</div>
<h1>Encryption works across the matrix.<br>Blind recovery has a narrower demonstrated scope.</h1>
<p>Measured synthetic-cipher evidence from real source texts. Known-key reversibility, blind key recovery and frozen-key transfer are reported separately.
No Voynich ciphertext was searched.</p><div class="cards">
<div class="card"><span class="number">{matrix['summary']['reference_exact']:,}/{matrix['summary']['cases']:,}</span>known-key cases exact</div>
<div class="card"><span class="number">{sum(r['engineering_gate_pass'] for r in initial)}/{len(initial)}</span>initial blind gates passed</div>
<div class="card"><span class="number">{sum(r['gate_pass'] for r in focused)}/{len(focused)}</span>focused blind gates passed</div>
<div class="card"><span class="number">{evidence['total_search_evaluations']:,}</span>scored candidates</div></div>
<p class="note"><strong>Interpretation boundary.</strong> A round trip demonstrates reversibility, not key discovery. An optimizer failure does not exclude a Voynich cipher family.
The follow-up changes length, budget and search constraints together; it is not an isolated ablation.</p>
<h2>1. Exact encryption and decryption</h2>
<p>Four works, three languages, 20 configurations per work, five seeds, and 120/300/600 prepared-character passages.
Independent reference and explorer decoders agree. Two-page six-table checks also passed:
{matrix['summary']['page_exact']}/{matrix['summary']['page_cases']}.</p>{sources}
<p>Supported variations: glyph, grouped and mixed whole-word coding; one/two homophones; fixed or prefix-free variable codes; preserved or encoded spaces.
Greek accents are stripped and final sigma is folded before a reversible 24-letter ASCII storage map.
The normalized text is recovered exactly; original accents and punctuation are not restored.</p>
<h3>Inspect concrete examples</h3>{examples}
<h2>2. Exhaustive finite recovery</h2>{finite_table}
<p>The shift search knows the family and alphabet but not the shift. The page search knows six tables but not which choices were used.
Both evaluate their entire declared finite space; neither result establishes arbitrary unknown-key recovery.
Independent-page optimization also agreed with exhaustive search where the model permits it.</p>
<h2>3. Original frozen blind benchmark</h2>
<p>32 positive cases and 96 matched controls, using 120/240 raw source characters, four chains and 500 proposals per chain.
Each search has 2,004 scored candidates including initialization. Gates require ≥95% development non-space accuracy,
≥90% frozen accuracy with full coverage, and lower development loss than every matched negative.</p>{means_table}
<p>Means across languages, keys and lengths are descriptive. A challenge label means active true codes/units are outside the bounded candidate inventory or code budget.
Invalid frozen decodes are scored as empty output (0%), not omitted.
The unseen-code count is an oracle-based diagnostic computed only after search: it measures true codes appearing in the reserved passage but absent
from development. A frozen partial key cannot translate such codes without an additional assumption or fitting step; we do not silently add one.</p>
<label for="filter">Filter cases</label><input id="filter" placeholder="e.g. latin-glyph">{baseline_table}
<h2>4. Focused substitution recovery</h2>
<p>This exploratory follow-up uses 600 prepared characters, four chains and 4,000 proposals per chain.
Injective proposals enforce the tested one-to-one cipher family. A direct glyph scorer is tested against the original objective.
One key is tested per work, with shuffled, message-free and block-order-mismatched controls using the same budget and selection rule.</p>
{focus_table}{recovered}
<h3>Paired proposal and length/budget ablations</h3>
<p>The follow-up above changes several factors together. These additional runs hold source starts, cipher keys, scorer and seeds fixed.
The generic proposal strategy is evaluated at all four combinations of 120/600 characters and 500/4,000 steps per chain.
The long/high-budget setting also supplies the paired comparison with injective proposals.
These are positive-only optimizer diagnostics; no matched-negative pass gate is assigned.</p>{ablation_table}
<p>There is one key per work. Passage length changes both the development and reserved lengths, so frozen percentages across lengths are not
measurements on the same held-out sample. These exploratory contrasts must be replicated before making general claims about optimizer power.</p>
<h2>5. Historical scope</h2>
<p><a href="https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Suetonius/12Caesars/Julius%2A.html#56">Suetonius, Julius 56.6</a>
describes Caesar's shifted-letter practice. Our exhaustive test instantiates that family on a modern 26-letter storage alphabet,
rather than claiming an exact reconstruction of Roman orthography.</p>
<p>Fifteenth-century letter/word substitution is documented in Penn's
<a href="https://bibliophilly.library.upenn.edu/viewer.php?id=LJS%20225">LJS 225 catalogue</a>, dated 1455–1458.
<a href="https://dspace.ut.ee/items/f4dc28f4-4367-4b62-b978-8fc696bf2a33">Marco Vito's HistoCrypt 2026 study</a>
discusses homophones and nomenclators in the same treatise. These establish family-level feasibility around the mid-fifteenth century,
not attestation of our exact keys or a pre-1438 date for every feature.</p>
<p>Our alphanumeric symbols, uniform homophone allocation, prefix-free codes and page dice policy are engineering constructions.
Greek/ASCII storage is modern preprocessing. No particular historical key has yet been reconstructed.</p>
<h2>6. Next research steps</h2>
<ol><li>Repeat successful recovery across additional keys, passages and independent authors.</li>
<li>Repeat the matched ablations across more keys and independent works; the present contrasts have one key per work.</li>
<li>Improve constrained homophonic search and qualify it on fixtures inside its actual search space.</li>
<li>Give grouped/mixed solvers explicit segmentation models and check inventory coverage first.</li>
<li>Reconstruct one documented historical key as a separate, historically attested benchmark.</li></ol>
<h2>7. Operational audit</h2>
<p>{len(evidence['runs'])} persisted searches, {evidence['total_search_evaluations']:,} scored candidates and {evidence['execution_errors']} captured evaluator errors.
Individual searches may be stopped at the evaluation limit while their planned benchmark is complete.
PostgreSQL stores IDs/checkpoints; local files preserve bounded candidate payloads.</p>
<p><a href="evidence.json">Operating evidence JSON</a> contains metrics, plans, source hashes, environments, run IDs and one selected winner per search.
It is not an every-proposal archive. All splits are within-work, not cross-author validation. The initial run used the clean framework revision;
follow-up development recorded dirty state and source hashes before commit. Match hashes when replaying.</p>
<footer>Classical editions: Perseus Digital Library / Trustees of Tufts University. Caesar: T. Rice Holmes (1914);
Homer: D. B. Monro and T. W. Allen (1908–1920). Pinned commits and CC BY-SA 4.0 licenses are retained in data/laboratory_sources.
Derived classical text excerpts are attributed and shared under CC BY-SA 4.0. Existing Alfonsi/Dante source provenance is recorded in acquisition code.</footer>
</main><script>document.getElementById('filter').addEventListener('input',e=>{{
const q=e.target.value.toLowerCase();document.querySelectorAll('#initial tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));
}});</script></html>"""
    (output/"report.html").write_text(content,encoding="utf-8")
    return output/"report.html"

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("roundtrips","baseline","focused","pages","shifts","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--ablation",type=Path,action="append",default=[])
    args=parser.parse_args()
    print(build_report(compile_evidence(args.roundtrips,args.baseline,args.focused,args.pages,args.shifts,args.ablation),args.output).resolve())
