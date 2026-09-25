"""Regression checks for the new experiment's inference-critical invariants."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("frontier", Path(__file__).with_name("06_boundary_frontier.py"))
f = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(f)


class FrontierTests(unittest.TestCase):
    def test_uncertainty_does_not_create_neighbours(self):
        words, gaps = f.parse_body("<%>daiin.?.chol<->or,y<$>")
        self.assertEqual([w["word"] for w in words], ["daiin", "?", "chol", "or", "y"])
        self.assertFalse(words[1]["clean"])
        self.assertEqual(gaps, ["ordinary", "ordinary", "drawing", "uncertain"])
        self.assertFalse(f.valid_pair(words[0], words[1]))

    def test_embedded_comments_and_alternatives(self):
        words, _ = f.parse_body("dai<!annotation>in.dai[{cto}:@194;]y")
        self.assertEqual(words[0], {"word": "daiin", "clean": True})
        self.assertEqual(words[1]["word"], "daictoy")
        self.assertFalse(words[1]["clean"])

    def test_folio_grouping_titles_and_paragraphs(self):
        text = """<f1r> <! $H=1 $L=A $I=H>
<f1r.1,@P0> <%>daiin.chol
<f1r.2,+P0> or.dal<$>
<f1r.3,*P0> <%>shol.chor
<f1r.4,=Pt> chol<$>
<f1r.5,+P0> daiin.chol
<f1v.1,@P0> <%>daiin.chol
"""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"sample.txt"
            p.write_text(text)
            lines = f.load_lines(p)
        self.assertEqual(len(lines), 5)
        self.assertEqual({ln["folio"] for ln in lines}, {"f1"})
        rows = f.observations(lines)
        self.assertEqual(sum(r["kind"] == "line" for r in rows), 1)
        self.assertEqual(sum(r["kind"] == "paragraph" for r in rows), 1)

    def test_terminal_is_never_a_feature(self):
        line = dict(locus="f1r.1",page="f1r",folio="f1",words=[{},{}],meta={},paragraph_start=False)
        a = f.record(line,0,"dain","chol","ordinary")
        b = f.record(line,0,"dair","chol","ordinary")
        self.assertEqual(f.features(a,context=True,identity=True), f.features(b,context=True,identity=True))

    def test_inline_hand_changes_persist_without_rewriting_history(self):
        text = """<f115r> <! $H=@ $L=B>
<f115r.1,@P0> <%><@H=2>daiin.chol
<f115r.2,+P0> daiin.chol
<f115r.3,+P0> <@H=3>daiin.chol
"""
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"sample.txt"
            p.write_text(text)
            lines=f.load_lines(p)
        self.assertEqual([ln["meta"]["H"] for ln in lines], ["2","2","3"])
        self.assertTrue(lines[0]["words"][0]["clean"])

    def test_pooled_selection_ignores_variant_distribution(self):
        def line(words):
            return dict(locus="f1r.1",page="f1r",folio="f1",words=[dict(word=w,clean=True) for w in words],meta={},paragraph_start=False)
        test = [line(["abnochy"])]
        a = f.hidden_candidates([line(["abn"]*6+["ochy"]*6)],test)
        b = f.hidden_candidates([line(["abl"]*6+["ochy"]*6)],test)
        self.assertEqual(a,b)
        self.assertEqual(a[0]["left"],"abn")
        self.assertEqual(a[0]["pooled_freq"],6)

    def test_folds_reproducible_and_balanced(self):
        values = [f"f{i}" for i in range(101)]
        a,b = f.assign_folds(values),f.assign_folds(reversed(values))
        self.assertEqual(a,b)
        counts = list(f.Counter(a.values()).values())
        self.assertLessEqual(max(counts)-min(counts),1)


if __name__ == "__main__":
    unittest.main()
