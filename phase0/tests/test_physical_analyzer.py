"""Tests for the physical (P1-P7) analyser.

These test the *plumbing and the safety behaviour*, not physical accuracy.  The
stand-in dataset under `fixtures/standin_physical/` is synthetic and is labelled as
such; nothing here asserts anything about real measurement performance.
"""
from __future__ import annotations

import csv
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import analyse_physical as ap                       # noqa: E402
import analyse_results as ar                        # noqa: E402

STANDIN = os.path.join(ROOT, "fixtures", "standin_physical")
PIDS = ["P%d" % i for i in range(1, 8)]

NOMINAL_COLS = ["run_id", "experiment", "variant", "source", "status", "safety_class",
                "panel_id", "device", "operator", "repeat", "h_mm", "lower_mm",
                "upper_mm", "true_h_mm", "design_h_mm", "burst_sd_mm",
                "failed_stage", "failed_gate"]


def write_dataset(dirpath, rows, manifest_runs=None, reference=None,
                  columns=NOMINAL_COLS):
    os.makedirs(dirpath, exist_ok=True)
    with open(os.path.join(dirpath, "results.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in columns})
    if manifest_runs is not None:
        from p0.core import dump_json
        dump_json(os.path.join(dirpath, "manifest_used.json"),
                  {"runs": manifest_runs})
    if reference is not None:
        cols = ["panel_id", "glyph_shape", "nominal_h_mm", "glyph_index", "method",
                "reference_h_mm"]
        with open(os.path.join(dirpath, "reference_table.csv"), "w", newline="",
                  encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in reference:
                w.writerow({c: r.get(c, "") for c in cols})


def nominal_row(run_id, panel, device, operator, repeat, h, ref, nominal_h,
                status="MEASURED", u=0.05):
    r = {"run_id": run_id, "experiment": "PHYSICAL_PILOT", "variant": "base",
         "source": "real", "status": status, "safety_class": "SAFE",
         "panel_id": panel, "device": device, "operator": operator,
         "repeat": repeat, "design_h_mm": nominal_h, "burst_sd_mm": 0.01}
    if status == "MEASURED":
        r.update({"h_mm": h, "lower_mm": h - 1.645 * u, "upper_mm": h + 1.645 * u,
                  "true_h_mm": ref})
    else:
        r.update({"true_h_mm": ref, "failed_stage": "IMAGE_QUALITY",
                  "failed_gate": "blur_sigma_mm"})
    return r


def manifest_run(run_id, panel, device, operator, repeat, safety="SAFE"):
    return {"run_id": run_id, "panel_id": panel, "device": device,
            "operator": operator, "repeat": repeat, "safety_class": safety}


class TestCriteriaParsing(unittest.TestCase):
    """Thresholds must come from the frozen document, not from this codebase."""

    def setUp(self):
        self.crits = ap.load_physical_criteria()

    def test_all_seven_present(self):
        self.assertEqual(sorted(self.crits), sorted(PIDS))

    def test_directions_and_values_match_document(self):
        for pid in ("P1", "P2", "P3", "P4", "P6"):
            self.assertEqual(self.crits[pid]["direction"], "LOWER_IS_BETTER", pid)
        self.assertEqual(self.crits["P5"]["direction"], "HIGHER_IS_BETTER")
        with open(os.path.join(ROOT, "docs", "P0_CRITERIA.md"),
                  encoding="utf-8") as fh:
            doc = fh.read()
        for pid in PIDS:
            self.assertIn(self.crits[pid]["go_raw"], doc)

    def test_population_hints_parsed(self):
        self.assertEqual(self.crits["P1"]["min_sample"], 15)
        self.assertEqual(self.crits["P2"]["class_nominal_mm"], 3.0)

    def test_p7_is_not_decidable(self):
        self.assertFalse(self.crits["P7"]["decidable"])
        self.assertIsNone(self.crits["P7"]["go"])

    def test_no_threshold_is_hardcoded(self):
        """Editing the criteria document must change the verdict."""
        with open(os.path.join(ROOT, "docs", "P0_CRITERIA.md"),
                  encoding="utf-8") as fh:
            doc = fh.read()
        loosened = doc.replace("| P2 | Residual SD after one global bias correction "
                               "(3 mm class) | <= 0.08 mm | 0.08-0.15 mm | > 0.15 mm |",
                               "| P2 | Residual SD after one global bias correction "
                               "(3 mm class) | <= 0.00001 mm | 0.00001-0.00002 mm | "
                               "> 0.00002 mm |")
        self.assertNotEqual(doc, loosened, "anchor line not found in the document")
        tmp = tempfile.mkdtemp()
        try:
            alt = os.path.join(tmp, "ALT_CRITERIA.md")
            with open(alt, "w", encoding="utf-8") as fh:
                fh.write(loosened)
            base = ap.analyse(STANDIN, os.path.join(tmp, "a"))
            tight = ap.analyse(STANDIN, os.path.join(tmp, "b"), criteria_path=alt)
            self.assertEqual(base["results"]["P2"]["status"], ap.PASS)
            self.assertEqual(tight["results"]["P2"]["status"], ap.FAIL)
            self.assertEqual(base["results"]["P2"]["statistics"],
                             tight["results"]["P2"]["statistics"])
        finally:
            shutil.rmtree(tmp)

    def test_parser_rejects_a_reshaped_table(self):
        tmp = tempfile.mkdtemp()
        try:
            bad = os.path.join(tmp, "BAD.md")
            with open(bad, "w", encoding="utf-8") as fh:
                fh.write("## Physical stage\n\n| ID | C | Go | Cond | Nogo |\n"
                         "|---|---|---|---|---|\n| P1 | x | maybe | y | z |\n")
            with self.assertRaises(ap.CriteriaError):
                ap.load_physical_criteria(bad)
        finally:
            shutil.rmtree(tmp)


class TestStandinDataset(unittest.TestCase):
    def test_standin_is_labelled_not_evidence(self):
        with open(os.path.join(STANDIN, "NOTICE.md"), encoding="utf-8") as fh:
            notice = fh.read()
        self.assertIn("NOT PHYSICAL EVIDENCE", notice)

    def test_physical_pilot_is_analysed(self):
        tmp = tempfile.mkdtemp()
        try:
            rep = ap.analyse(STANDIN, tmp)
            self.assertEqual(rep["dataset"]["physical_rows"], 32)
            self.assertTrue(os.path.exists(
                os.path.join(tmp, "analysis_physical.json")))
        finally:
            shutil.rmtree(tmp)

    def test_all_seven_criteria_get_a_status(self):
        tmp = tempfile.mkdtemp()
        try:
            rep = ap.analyse(STANDIN, tmp)
            for pid in PIDS:
                r = rep["results"][pid]
                self.assertIn(r["status"],
                              (ap.PASS, ap.CONDITIONAL, ap.FAIL, ap.UNCOMPUTABLE), pid)
                self.assertIn("go", r["threshold_reference"], pid)
                self.assertIn("population", r, pid)
                if r["status"] == ap.UNCOMPUTABLE:
                    self.assertTrue(r["reason"], "%s must explain itself" % pid)
        finally:
            shutil.rmtree(tmp)

    def test_abstentions_are_preserved_in_denominators(self):
        tmp = tempfile.mkdtemp()
        try:
            rep = ap.analyse(STANDIN, tmp)
            p5 = rep["results"]["P5"]
            self.assertEqual(p5["population"]["attempted"], 24)
            self.assertEqual(p5["population"]["abstained"], 1)
            self.assertEqual(p5["population"]["measured"], 23)
            self.assertIn("blur_sigma_mm", p5["population"]["abstention_reasons"])
            p6 = rep["results"]["P6"]
            self.assertEqual(p6["population"]["attempted"], 8)
            self.assertEqual(p6["population"]["abstained"], 7)
        finally:
            shutil.rmtree(tmp)

    def test_deterministic_output(self):
        tmp = tempfile.mkdtemp()
        try:
            a = ap.analyse(STANDIN, os.path.join(tmp, "a"))
            b = ap.analyse(STANDIN, os.path.join(tmp, "b"))
            self.assertEqual(a["results"], b["results"])
            self.assertEqual(a["tally"], b["tally"])
            with open(os.path.join(tmp, "a", "analysis_physical.json"),
                      encoding="utf-8") as fh:
                fa = fh.read()
            with open(os.path.join(tmp, "b", "analysis_physical.json"),
                      encoding="utf-8") as fh:
                fb = fh.read()
            self.assertEqual(fa, fb)
        finally:
            shutil.rmtree(tmp)


class TestMissingData(unittest.TestCase):
    """Missing physical data must never become zero and never become PASS."""

    def _base_rows(self, n_panels=1, status_override=None):
        rows, runs = [], []
        for p, nom, ref in (("P01", 3.0, 3.04), ("P02", 2.0, 2.03))[:n_panels]:
            for dev in ("A", "B"):
                for op in ("OP1", "OP2"):
                    for rep in ("R1", "R2", "R3"):
                        rid = "%s-%s-%s-%s" % (p, dev, op, rep)
                        st = status_override or "MEASURED"
                        rows.append(nominal_row(rid, p, dev, op, rep, ref + 0.01,
                                                ref, nom, status=st))
                        runs.append(manifest_run(rid, p, dev, op, rep))
        return rows, runs

    def test_missing_reference_table_makes_p1_uncomputable(self):
        tmp = tempfile.mkdtemp()
        try:
            rows, runs = self._base_rows()
            write_dataset(os.path.join(tmp, "ds"), rows, runs, reference=None)
            rep = ap.analyse(os.path.join(tmp, "ds"), os.path.join(tmp, "out"))
            p1 = rep["results"]["P1"]
            self.assertEqual(p1["status"], ap.UNCOMPUTABLE)
            self.assertIn("reference_table", p1["reason"])
            self.assertEqual(p1["statistics"], {})
        finally:
            shutil.rmtree(tmp)

    def test_too_few_cross_checked_glyphs_is_uncomputable_not_pass(self):
        tmp = tempfile.mkdtemp()
        try:
            rows, runs = self._base_rows()
            ref = []
            for i in range(3):                      # far fewer than the required 15
                for m in ("SCANNER_2400DPI", "MICROSCOPE"):
                    ref.append({"panel_id": "P01", "glyph_shape": "BAR_I",
                                "nominal_h_mm": 3.0, "glyph_index": i,
                                "method": m, "reference_h_mm": 3.04})
            write_dataset(os.path.join(tmp, "ds"), rows, runs, reference=ref)
            rep = ap.analyse(os.path.join(tmp, "ds"), os.path.join(tmp, "out"))
            p1 = rep["results"]["P1"]
            self.assertEqual(p1["status"], ap.UNCOMPUTABLE)
            self.assertIn("15", p1["reason"])
            # the statistic is 0.0 here, which must NOT be read as a pass
            self.assertEqual(p1["statistics"]["mean_abs_difference_mm"], 0.0)
        finally:
            shutil.rmtree(tmp)

    def test_missing_reference_value_blocks_p2_and_p4(self):
        tmp = tempfile.mkdtemp()
        try:
            rows, runs = self._base_rows()
            rows[0]["true_h_mm"] = ""               # one reference value absent
            write_dataset(os.path.join(tmp, "ds"), rows, runs)
            rep = ap.analyse(os.path.join(tmp, "ds"), os.path.join(tmp, "out"))
            for pid in ("P2", "P4"):
                r = rep["results"][pid]
                self.assertEqual(r["status"], ap.UNCOMPUTABLE, pid)
                self.assertIn("reference", r["reason"])
                self.assertNotIn("class_residual_sd_mm", r["statistics"])
                self.assertNotIn("abs_inter_device_bias_mm", r["statistics"])
            self.assertEqual(rep["results"]["P2"]["population"]
                             ["measured_missing_reference"], 1)
        finally:
            shutil.rmtree(tmp)

    def test_absent_3mm_class_is_uncomputable(self):
        tmp = tempfile.mkdtemp()
        try:
            rows, runs = [], []
            for dev in ("A", "B"):
                for op in ("OP1", "OP2"):
                    for rep in ("R1", "R2", "R3"):
                        rid = "P02-%s-%s-%s" % (dev, op, rep)
                        rows.append(nominal_row(rid, "P02", dev, op, rep, 2.04,
                                                2.03, 2.0))
                        runs.append(manifest_run(rid, "P02", dev, op, rep))
            write_dataset(os.path.join(tmp, "ds"), rows, runs)
            rep = ap.analyse(os.path.join(tmp, "ds"), os.path.join(tmp, "out"))
            p2 = rep["results"]["P2"]
            self.assertEqual(p2["status"], ap.UNCOMPUTABLE)
            self.assertEqual(p2["population"]["class_rows"], 0)
            self.assertIsNone(p2["statistics"]["class_residual_sd_mm"])
        finally:
            shutil.rmtree(tmp)

    def test_incomplete_block_is_uncomputable_not_pass(self):
        tmp = tempfile.mkdtemp()
        try:
            rows, runs = self._base_rows()
            extra = manifest_run("P01-A-OP1-R9", "P01", "A", "OP1", "R9")
            write_dataset(os.path.join(tmp, "ds"), rows, runs + [extra] * 6)
            rep = ap.analyse(os.path.join(tmp, "ds"), os.path.join(tmp, "out"))
            p5 = rep["results"]["P5"]
            self.assertEqual(p5["status"], ap.UNCOMPUTABLE)
            self.assertIn("incomplete", p5["reason"])
            self.assertEqual(p5["statistics"]["acceptance_rate"], 1.0)
        finally:
            shutil.rmtree(tmp)

    def test_no_stress_block_is_uncomputable(self):
        tmp = tempfile.mkdtemp()
        try:
            rows, runs = self._base_rows()
            write_dataset(os.path.join(tmp, "ds"), rows, runs)
            rep = ap.analyse(os.path.join(tmp, "ds"), os.path.join(tmp, "out"))
            p6 = rep["results"]["P6"]
            self.assertEqual(p6["status"], ap.UNCOMPUTABLE)
            self.assertEqual(p6["population"]["attempted"], 0)
            self.assertEqual(p6["statistics"], {})
        finally:
            shutil.rmtree(tmp)

    def test_single_device_makes_p4_uncomputable(self):
        tmp = tempfile.mkdtemp()
        try:
            rows, runs = [], []
            for op in ("OP1", "OP2"):
                for rep in ("R1", "R2", "R3"):
                    rid = "P01-A-%s-%s" % (op, rep)
                    rows.append(nominal_row(rid, "P01", "A", op, rep, 3.05, 3.04, 3.0))
                    runs.append(manifest_run(rid, "P01", "A", op, rep))
            write_dataset(os.path.join(tmp, "ds"), rows, runs)
            rep = ap.analyse(os.path.join(tmp, "ds"), os.path.join(tmp, "out"))
            p4 = rep["results"]["P4"]
            self.assertEqual(p4["status"], ap.UNCOMPUTABLE)
            self.assertIn("2 devices", p4["reason"])
        finally:
            shutil.rmtree(tmp)

    def test_all_abstained_keeps_p5_computable_and_fails(self):
        """Abstention is an observed outcome, not an implementation failure."""
        tmp = tempfile.mkdtemp()
        try:
            rows, runs = self._base_rows(status_override="PHYSICAL_SIZE_NOT_"
                                                         "ESTABLISHED_IMAGE_QUALITY")
            write_dataset(os.path.join(tmp, "ds"), rows, runs)
            rep = ap.analyse(os.path.join(tmp, "ds"), os.path.join(tmp, "out"))
            p5 = rep["results"]["P5"]
            self.assertEqual(p5["status"], ap.FAIL)
            self.assertEqual(p5["statistics"]["acceptance_rate"], 0.0)
            self.assertEqual(p5["population"]["abstained"], 12)
        finally:
            shutil.rmtree(tmp)

    def test_missing_required_column_is_refused(self):
        tmp = tempfile.mkdtemp()
        try:
            rows, runs = self._base_rows()
            cols = [c for c in NOMINAL_COLS if c != "true_h_mm"]
            write_dataset(os.path.join(tmp, "ds"), rows, runs, columns=cols)
            with self.assertRaises(ap.DatasetError):
                ap.analyse(os.path.join(tmp, "ds"), os.path.join(tmp, "out"))
        finally:
            shutil.rmtree(tmp)


class TestRoutingAndSyntheticUnchanged(unittest.TestCase):
    def test_safe_accuracy_experiments_semantics_unchanged(self):
        self.assertEqual(ar.SAFE_ACCURACY_EXPERIMENTS,
                         ("E_NOMINAL", "E_INKSPREAD", "E_ILLUM", "E_THICKNESS"))

    def test_synthetic_criteria_constants_unchanged(self):
        self.assertEqual(ar.CRIT, {
            "C1_math_max_abs_err_mm": 0.010,
            "C2_bias_abs_mm": 0.030,
            "C2_p95_abs_err_mm": 0.060,
            "C3_repeatability_sd_mm": 0.030,
            "C4_min_coverage": 0.90,
            "C7_unsafe_detectable_abstention": 1.00,
            "C8_max_false_clear": 0,
            "C11_min_safe_measure_rate": 0.80,
        })

    def test_router_sends_physical_dataset_to_physical_analyser(self):
        tmp = tempfile.mkdtemp()
        try:
            rc = ar.main(["--in", STANDIN, "--out", tmp])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(
                os.path.join(tmp, "analysis_physical.json")))
        finally:
            shutil.rmtree(tmp)

    def test_router_refuses_mixed_dataset(self):
        tmp = tempfile.mkdtemp()
        try:
            rows, runs = [], []
            for rep in ("R1", "R2"):
                rid = "P01-A-OP1-%s" % rep
                rows.append(nominal_row(rid, "P01", "A", "OP1", rep, 3.05, 3.04, 3.0))
                runs.append(manifest_run(rid, "P01", "A", "OP1", rep))
            rows.append({"run_id": "E_NOMINAL-BAR_I-3.0__base",
                         "experiment": "E_NOMINAL", "variant": "base",
                         "source": "synthetic", "status": "MEASURED",
                         "safety_class": "SAFE", "panel_id": "", "device": "",
                         "operator": "", "repeat": "", "h_mm": 3.05,
                         "lower_mm": 3.0, "upper_mm": 3.1, "true_h_mm": 3.04,
                         "design_h_mm": 3.0})
            write_dataset(os.path.join(tmp, "ds"), rows, runs)
            rc = ar.main(["--in", os.path.join(tmp, "ds"), "--out",
                          os.path.join(tmp, "out")])
            self.assertEqual(rc, 2)
        finally:
            shutil.rmtree(tmp)

    def test_purely_synthetic_dataset_still_uses_c_criteria(self):
        synth = os.path.join(ROOT, "out", "synthetic")
        if not os.path.exists(os.path.join(synth, "results.csv")):
            self.skipTest("committed synthetic result set not present")
        tmp = tempfile.mkdtemp()
        try:
            rc = ar.main(["--in", synth, "--out", tmp])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(tmp, "analysis.json")))
            self.assertFalse(os.path.exists(
                os.path.join(tmp, "analysis_physical.json")))
            import json
            with open(os.path.join(tmp, "analysis.json"), encoding="utf-8") as fh:
                new = json.load(fh)
            with open(os.path.join(synth, "analysis", "analysis.json"),
                      encoding="utf-8") as fh:
                old = json.load(fh)
            self.assertEqual(new["verdict"], old["verdict"])
            self.assertEqual(new["criteria"], old["criteria"])
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
