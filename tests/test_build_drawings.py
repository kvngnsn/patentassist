"""Offline tests for scripts/drawings.py (figures.json -> SVG + 37 CFR 1.84 PDF sheets)."""

import copy
import json
import os
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
FIX = os.path.join(HERE, "fixtures", "build")
sys.path.insert(0, SCRIPTS)

import drawings  # noqa: E402

try:
    import reportlab  # noqa: F401
    HAVE_RL = True
except ImportError:
    HAVE_RL = False
try:
    import fitz  # noqa: F401
    HAVE_FITZ = True
except ImportError:
    HAVE_FITZ = False

PT_PER_CM = 72.0 / 2.54
MIN_CAP_PT = 0.32 * PT_PER_CM


def load_fixture():
    with open(os.path.join(FIX, "figures.json"), encoding="utf-8") as fh:
        return json.load(fh)


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return path


@unittest.skipUnless(HAVE_RL, "reportlab not installed")
class DrawingsBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="pa-draw-test-")
        cls.res = drawings.build(os.path.join(FIX, "figures.json"), cls.tmp, d=None, no_audit=True)
        with open(cls.res["manifest"], encoding="utf-8") as fh:
            cls.man = json.load(fh)
        cls.figs = {f["id"]: f for f in cls.man["figures"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_build_ok(self):
        self.assertTrue(self.res["ok"], self.res["findings"])
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "drawings.pdf")))
        self.assertEqual(self.man["schema"], "patentassist/drawings-manifest@1")
        self.assertEqual(len(self.man["figures"]), 5)

    def test_manifest_numerals(self):
        nums = lambda fid: sorted(n["numeral"] for n in self.figs[fid]["numerals"])  # noqa: E731
        self.assertEqual(nums("FIG. 1"), ["100", "110", "120", "130", "140", "150", "160"])
        self.assertEqual(nums("FIG. 2"), ["202", "204", "206", "208", "210", "212", "214"])
        self.assertEqual(nums("FIG. 3"), ["110", "120", "140", "150", "302", "304", "306", "308", "310"])
        self.assertEqual(nums("FIG. 4"), ["160", "402", "404", "406", "408", "410"])

    def test_text_heights_at_least_032_cm(self):
        for f in self.man["figures"]:
            self.assertGreaterEqual(f["min_cap_height_cm"], 0.32, f["id"])
            self.assertGreaterEqual(f["scale"], 0.0)

    def test_content_inside_sight(self):
        sx0, sy0, sx1, sy1 = self.man["sheet"]["sight_pt"]
        for f in self.man["figures"]:
            x0, y0, x1, y1 = f["bbox_pt"]
            self.assertGreaterEqual(x0, sx0, f["id"])
            self.assertGreaterEqual(y0, sy0, f["id"])
            self.assertLessEqual(x1, sx1, f["id"])
            self.assertLessEqual(y1, sy1, f["id"])
            for n in f["numerals"]:
                b = n["text_bbox_pt"]
                self.assertTrue(sx0 <= b[0] and b[2] <= sx1 and sy0 <= b[1] and b[3] <= sy1, (f["id"], n))

    def test_letter_sight_matches_rule(self):
        # 1.84(g): sight no greater than 17.6 x 24.4 cm on letter
        sx0, sy0, sx1, sy1 = self.man["sheet"]["sight_pt"]
        self.assertAlmostEqual((sx1 - sx0) / PT_PER_CM, 17.6, delta=0.05)
        self.assertAlmostEqual((sy1 - sy0) / PT_PER_CM, 24.4, delta=0.05)

    def test_svgs_parse(self):
        for name in self.man["svgs"]:
            root = ET.parse(os.path.join(self.tmp, name)).getroot()
            self.assertTrue(root.tag.endswith("svg"))
            s = read_text(os.path.join(self.tmp, name))
            for bad in ("#ff", "red", "blue", "rgb("):
                self.assertNotIn('stroke="%s' % bad, s)

    @unittest.skipUnless(HAVE_FITZ, "PyMuPDF not installed")
    def test_pdf_rules(self):
        doc = fitz.open(os.path.join(self.tmp, "drawings.pdf"))
        n = len(doc)
        self.assertEqual(n, self.res["sheets"])
        alltext = []
        for i, page in enumerate(doc):
            self.assertAlmostEqual(page.rect.width, 612, delta=1)
            self.assertAlmostEqual(page.rect.height, 792, delta=1)
            sx0, sy0 = 2.5 * PT_PER_CM, 2.5 * PT_PER_CM
            sx1, sy1 = page.rect.width - 1.5 * PT_PER_CM, page.rect.height - 1.0 * PT_PER_CM
            for d in page.get_drawings():
                r = d["rect"]
                self.assertTrue(r.x0 >= sx0 - 0.5 and r.y0 >= sy0 - 0.5 and r.x1 <= sx1 + 0.5 and r.y1 <= sy1 + 0.5,
                                "drawing outside sight on sheet %d: %s" % (i + 1, r))
                for key in ("color", "fill"):
                    c = d.get(key)
                    if c is not None:
                        self.assertTrue(all(v < 0.02 for v in c), "non-black %s %s" % (key, c))
            spans = [s for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]
            for s in spans:
                if s["text"].strip():
                    self.assertGreaterEqual(s["size"] * drawings.CAP_RATIO, MIN_CAP_PT - 0.01, s["text"])
                    self.assertEqual(s.get("color", 0), 0)
            texts = [s["text"].strip() for s in spans]
            alltext += texts
            self.assertIn("%d/%d" % (i + 1, n), texts, "sheet number 1.84(t)")
        for k in range(1, 6):
            self.assertIn("FIG. %d" % k, alltext)
        for f in doc.get_page_fonts(0):
            self.assertNotEqual(f[1], "n/a", "font %s not embedded" % f[3])

    def test_sheet_number_inside_sight_and_larger_than_numerals(self):
        self.assertGreater(drawings.SHEETNO_SIZE, drawings.NUM_SIZE)
        self.assertGreater(drawings.FIG_SIZE, drawings.NUM_SIZE)


class LayoutUnitTest(unittest.TestCase):
    def test_flowchart_has_decision_diamond_and_branch_labels(self):
        f = load_fixture()["figures"][1]
        fig = drawings.layout_flowchart(f, "upper")
        diamonds = [it for it in fig.items if it["t"] == "poly" and not it.get("fill") and len(it["pts"]) == 4]
        self.assertEqual(len(diamonds), 2)
        texts = [it["s"] for it in fig.items if it["t"] == "text"]
        for lab in ("LEFT", "RIGHT", "YES", "NO"):
            self.assertIn(lab, texts)
        arrows = [it for it in fig.items if it["t"] == "poly" and it.get("fill")]
        self.assertGreaterEqual(len(arrows), 6)
        self.assertEqual(sorted(n["numeral"] for n in fig.numerals), [str(x) for x in range(202, 215, 2)])

    def test_block_nesting_container_encloses_children(self):
        f = load_fixture()["figures"][0]
        fig = drawings.layout_block(f, "upper")
        rects = [it for it in fig.items if it["t"] == "rect"]
        # biggest rect is the HELMET container; the four children sit inside it
        rects.sort(key=lambda r: -r["w"] * r["h"])
        cont = rects[0]
        labels = {}
        for it in fig.items:
            if it["t"] == "text":
                labels.setdefault(it["s"], it)
        inside = 0
        for r in rects[1:]:
            if (r["x"] >= cont["x"] and r["y"] >= cont["y"] and r["x"] + r["w"] <= cont["x"] + cont["w"]
                    and r["y"] + r["h"] <= cont["y"] + cont["h"]):
                inside += 1
        self.assertEqual(inside, 4)
        self.assertIn("HELMET", labels)

    def test_text_case_as_is(self):
        f = copy.deepcopy(load_fixture()["figures"][1])
        fig = drawings.layout_flowchart(f, "as_is")
        self.assertIn("Power on controller", [it["s"] for it in fig.items if it["t"] == "text"])

    def test_fit_text_never_below_minimum_and_never_splits_words(self):
        size, lines = drawings.fit_text("Extraordinarily longwordedcomponentname here", 60.0)
        self.assertGreaterEqual(size, drawings.TEXT_MIN)
        self.assertIn("longwordedcomponentname", " ".join(lines).split())

    def test_unknown_step_target(self):
        f = {"id": "FIG. 9", "type": "flowchart", "steps": [{"numeral": 1, "label": "a", "next": 99}]}
        with self.assertRaises(drawings.UsageError):
            drawings.layout_flowchart(f, "upper")


@unittest.skipUnless(HAVE_RL, "reportlab not installed")
class DrawingsFindingsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pa-draw-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_single_view_has_no_fig_label(self):
        data = load_fixture()
        data["figures"] = [data["figures"][1]]
        p = write_json(os.path.join(self.tmp, "figures.json"), data)
        res = drawings.build(p, os.path.join(self.tmp, "out"), d=None, no_audit=True)
        with open(res["manifest"], encoding="utf-8") as fh:
            man = json.load(fh)
        self.assertTrue(man["single_view"])
        self.assertIsNone(man["figures"][0]["fig_label"])
        svg = read_text(res["svgs"][0])
        self.assertNotIn("FIG.", svg)   # 1.84(u)(1)

    def test_numeral_reused_for_different_part_blocks(self):
        data = load_fixture()
        data["figures"][1]["steps"][0]["numeral"] = 110     # 110 is the controller in FIG. 1
        p = write_json(os.path.join(self.tmp, "figures.json"), data)
        res = drawings.build(p, os.path.join(self.tmp, "out"), d=None, no_audit=True)
        self.assertIn("numeral-reused", [f["code"] for f in res["findings"] if f["level"] == "BLOCK"])

    def test_oversized_flowchart_blocks(self):
        steps = [{"numeral": 600 + 2 * i, "label": "Perform processing operation number %d on the data" % i}
                 for i in range(30)]
        data = {"schema": "patentassist/figures@1", "figures": [
            {"id": "FIG. 1", "type": "flowchart", "steps": steps},
            {"id": "FIG. 2", "type": "flowchart", "steps": steps[:2]}]}
        p = write_json(os.path.join(self.tmp, "figures.json"), data)
        res = drawings.build(p, os.path.join(self.tmp, "out"), d=None, no_audit=True)
        self.assertIn("figure-too-large", [f["code"] for f in res["findings"]])
        self.assertFalse(res["ok"])

    def test_bad_schema_rejected(self):
        p = write_json(os.path.join(self.tmp, "figures.json"), {"schema": "patentassist/figures@2", "figures": []})
        with self.assertRaises(drawings.UsageError):
            drawings.build(p, os.path.join(self.tmp, "out"), d=None, no_audit=True)

    def test_graph_and_image_types(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow not installed")
        img = Image.new("RGB", (200, 120), (240, 240, 240))
        dr = ImageDraw.Draw(img)
        dr.rectangle([20, 20, 180, 100], outline=(30, 30, 200), width=4)
        img.save(os.path.join(self.tmp, "sketch.png"))
        data = {"schema": "patentassist/figures@1", "figures": [
            {"id": "FIG. 1", "type": "image", "path": "sketch.png",
             "numerals": [{"numeral": 700, "label": "housing", "x": 0.1, "y": 0.2},
                          {"numeral": 702, "label": "lid", "x": 0.9, "y": 0.5}]},
            {"id": "FIG. 2", "type": "graph", "kind": "bar", "x_label": "mode", "y_label": "current",
             "bars": [{"label": "idle", "value": 2}, {"label": "flash", "value": 9, "numeral": 704}]}]}
        p = write_json(os.path.join(self.tmp, "figures.json"), data)
        res = drawings.build(p, os.path.join(self.tmp, "out"), d=None, no_audit=True)
        self.assertTrue(res["ok"], res["findings"])
        art = os.path.join(self.tmp, "out", "FIG-1-lineart.png")
        self.assertTrue(os.path.exists(art))
        with Image.open(art) as im:
            self.assertEqual(im.mode, "1")   # black-and-white line art


if __name__ == "__main__":
    unittest.main()


class EdgeRoutingTest(unittest.TestCase):
    """F03: a connector into a nested box ran straight through a sibling box (BATTERY) and both scripts
    said "no blocking issues". F35: its label sat beside the wrong box."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        with open(os.path.join(FIX, "line_through_box_figures.json"), encoding="utf-8") as fh:
            self.spec = json.load(fh)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_seg_hits_rect(self):
        r = (0, 0, 10, 10)
        self.assertTrue(drawings.seg_hits_rect((5, -5), (5, 15), r))
        self.assertFalse(drawings.seg_hits_rect((-5, -5), (-5, 15), r))
        self.assertFalse(drawings.seg_hits_rect((0, -5), (0, 15), r))      # along the border: not inside
        self.assertTrue(drawings.seg_hits_rect((-5, -5), (15, 15), r))     # diagonal

    def test_repro_edge_routed_around_battery(self):
        fig = drawings.layout_block(self.spec["figures"][0], "upper")
        self.assertEqual(drawings.edge_crossings(fig.nodes, fig.edges, fig.numerals), [])
        sig = [e for e in fig.edges if e["from"] == "sensor"][0]
        batt = [n for n in fig.nodes if n["id"] == "batt"][0]["box"]
        self.assertFalse(any(drawings.seg_hits_rect(a, b, batt) for a, b in zip(sig["pts"], sig["pts"][1:])))
        # every segment is horizontal or vertical
        for a, b in zip(sig["pts"], sig["pts"][1:]):
            self.assertTrue(abs(a[0] - b[0]) < 0.01 or abs(a[1] - b[1]) < 0.01)

    def test_label_beside_longest_run_of_its_own_line(self):
        fig = drawings.layout_block(self.spec["figures"][0], "upper")
        lab = [el for el in fig.edge_labels if el["text"] == "SIGNAL"][0]
        sig = fig.edges[lab["edge"]]
        segs = list(zip(sig["pts"], sig["pts"][1:]))
        bx = lab["box"]
        cy = (bx[1] + bx[3]) / 2.0

        def beside(sg):   # within 12 pt of a vertical run of its own connector, level with it
            (x0, y0), (x1, y1) = sg
            return abs(x0 - x1) < 0.01 and min(abs(bx[0] - x0), abs(bx[2] - x0)) < 12.0 and \
                min(y0, y1) <= cy <= max(y0, y1)
        self.assertTrue(any(beside(sg) for sg in segs), (bx, segs))
        # inside the housing container, not straddling its border
        house = [n for n in fig.nodes if n["id"] == "housing"][0]["box"]
        self.assertTrue(house[1] < bx[1] and bx[3] < house[3])
        batt = [n for n in fig.nodes if n["id"] == "batt"][0]["box"]
        self.assertFalse(bx[0] < batt[2] and batt[0] < bx[2] and bx[1] < batt[3] and batt[1] < bx[3])

    def test_manifest_geometry_and_check_flags_a_crossing(self):
        import check_drawings
        res = drawings.build(os.path.join(FIX, "line_through_box_figures.json"), self.tmp, d=self.tmp, no_audit=True)
        self.assertFalse([f for f in res["findings"] if f["code"].startswith("EDGE_CROSSES")], res["findings"])
        man_p = os.path.join(self.tmp, "drawings-manifest.json")
        with open(man_p) as fh:
            man = json.load(fh)
        mf = man["figures"][0]
        self.assertTrue(mf["nodes"] and mf["edges"] and mf["edge_labels"])
        self.assertIn("box_pt", mf["nodes"][0])
        self.assertIn("pts_pt", mf["edges"][0])
        spec = os.path.join(FIX, "line_through_box_spec.md")
        figs = os.path.join(FIX, "line_through_box_figures.json")
        ok = check_drawings.check(figs, spec, man_p, None)
        self.assertIn("edge-crossings", ok["checks_run"])
        self.assertFalse([f for f in ok["findings"] if f["code"].startswith("EDGE_CROSSES")])
        # the old straight route: from the sensor straight down to the controller, through the battery
        sig = [e for e in mf["edges"] if e["from"] == "sensor"][0]
        sig["pts_pt"] = [sig["pts_pt"][0], [sig["pts_pt"][0][0], sig["pts_pt"][-1][1]]]
        bat = [n for n in mf["nodes"] if n["id"] == "batt"][0]["box_pt"]
        x = (bat[0] + bat[2]) / 2.0
        sig["pts_pt"] = [[x, sig["pts_pt"][0][1]], [x, sig["pts_pt"][-1][1]]]
        num = [n for n in mf["numerals"] if n["numeral"] == "138"][0]["text_bbox_pt"]
        mf["edges"].append({"from": "xcvr", "to": "sensor", "label": "",
                            "pts_pt": [[(num[0] + num[2]) / 2.0, num[1] - 5], [(num[0] + num[2]) / 2.0, num[3] + 5]]})
        bad_p = os.path.join(self.tmp, "bad-manifest.json")
        with open(bad_p, "w") as fh:
            json.dump(man, fh)
        bad = check_drawings.check(figs, spec, bad_p, None)
        codes = [(f["level"], f["code"]) for f in bad["findings"]]
        self.assertIn(("BLOCK", "EDGE_CROSSES_NODE"), codes)
        self.assertIn(("WARN", "EDGE_CROSSES_NUMERAL"), codes)


class LayoutOptionsTest(unittest.TestCase):
    """F32 (direction fallback), F33 (unknown keys), F34 (connectors, size budget)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def build(self, figs):
        p = os.path.join(self.tmp, "figures.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(dict({"schema": "patentassist/figures@1", "sheet": "letter"}, **figs), fh)
        return drawings.build(p, os.path.join(self.tmp, "out"), d=self.tmp, no_audit=True)

    def test_unknown_keys_warn(self):
        res = self.build({"figures": [{"id": "FIG. 1", "type": "flowchart", "colour": "red",
                                       "steps": [{"numeral": 10, "label": "Go", "nxt": 12}, {"numeral": 12, "label": "Stop",
                                                                                            "kind": "finish"}]}],
                          "_comment": "ignored", "papersize": "a4"})
        msgs = [f["message"] for f in res["findings"] if f["code"] == "unknown-key"]
        self.assertTrue(any("'colour'" in m for m in msgs), msgs)
        self.assertTrue(any("'nxt'" in m for m in msgs), msgs)
        self.assertTrue(any("'papersize'" in m for m in msgs), msgs)
        self.assertTrue(any("'finish'" in m for m in msgs), msgs)
        self.assertFalse(any("_comment" in m for m in msgs))

    def test_documented_fixture_has_no_unknown_keys(self):
        res = drawings.build(os.path.join(FIX, "figures.json"), os.path.join(self.tmp, "o"), d=self.tmp, no_audit=True)
        self.assertFalse([f for f in res["findings"] if f["code"] == "unknown-key"], res["findings"])

    def test_connector_steps_split_a_flowchart(self):
        res = self.build({"figures": [
            {"id": "FIG. 3A", "type": "flowchart", "steps": [
                {"numeral": 302, "label": "Start", "kind": "start"},
                {"numeral": 304, "label": "Signature persists?", "kind": "decision", "yes": "A", "no": 302},
                {"kind": "connector", "label": "A"}]},
            {"id": "FIG. 3B", "type": "flowchart", "steps": [
                {"kind": "connector", "label": "A"}, {"numeral": 310, "label": "Reduce power", "kind": "end"}]}]})
        self.assertEqual(res["summary"]["blocking"], 0, res["findings"])
        self.assertFalse([f for f in res["findings"] if f["code"].startswith("connector")])
        fig = drawings.layout_flowchart({"id": "FIG. 3B", "steps": [{"kind": "connector", "label": "A"},
                                                                   {"numeral": 310, "label": "Reduce power"}]}, "upper")
        self.assertTrue(any(it["t"] == "circle" for it in fig.items))
        self.assertTrue(any(it["t"] == "text" and it["s"] == "A" for it in fig.items))
        self.assertEqual([n["numeral"] for n in fig.numerals], ["310"])

    def test_unpaired_connector_warns(self):
        res = self.build({"figures": [{"id": "FIG. 1", "type": "flowchart", "steps": [
            {"numeral": 10, "label": "Go"}, {"kind": "connector", "label": "B"}]}]})
        self.assertIn("connector-unpaired", [f["code"] for f in res["findings"]])

    def test_size_budget_for_long_flowchart(self):
        steps = [{"numeral": 400 + 2 * i, "label": "Step number %d" % i} for i in range(16)]
        res = self.build({"figures": [{"id": "FIG. 1", "type": "flowchart", "steps": steps},
                                      {"id": "FIG. 2", "type": "flowchart", "steps": steps[:3]}]})
        b = {x["id"]: x for x in res["budget"]}
        self.assertFalse(b["FIG. 1"]["fits"])
        self.assertLess(b["FIG. 1"]["capacity"], 16)
        self.assertIn("connector", b["FIG. 1"]["message"])
        self.assertTrue(b["FIG. 2"]["fits"])
        with open(os.path.join(self.tmp, "out", "drawings-manifest.json")) as fh:
            man = json.load(fh)
        self.assertEqual(len(man["budget"]), 2)

    def test_direction_keeps_larger_scale_when_neither_fits(self):
        nodes = [{"id": "n%d" % i, "label": "Component number %d with a long label" % i, "numeral": 100 + 2 * i}
                 for i in range(14)]
        edges = [{"from": "n%d" % i, "to": "n%d" % (i + 1)} for i in range(13)]
        res = self.build({"figures": [{"id": "FIG. 1", "type": "block", "direction": "LR", "nodes": nodes,
                                       "edges": edges}]})
        info = [f for f in res["findings"] if f["code"] in ("direction-kept", "direction-changed")]
        self.assertEqual(len(info), 1, res["findings"])
        if info[0]["code"] == "direction-kept":
            import re as _re
            s = [float(x) for x in _re.findall(r"scale (\d\.\d\d)", info[0]["message"])]
            kept = "top-to-bottom" if "kept top-to-bottom" in info[0]["message"] else "left-to-right"
            self.assertEqual(kept == "top-to-bottom", s[1] > s[0])
