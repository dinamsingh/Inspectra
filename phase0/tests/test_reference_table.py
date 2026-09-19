"""Tests for reference-table schema validation (blocker B2).

These test **schema and independence enforcement only**.  No test in this file asserts
anything about physical measurement accuracy, and no file here is ground truth: tables
are built inline in temporary directories purely to exercise validator branches.
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

import validate_reference_table as vrt            # noqa: E402

STANDIN_TABLE = os.path.join(ROOT, "fixtures", "standin_physical",
                             "reference_table.csv")


def ref_row(panel="P01", shape="BAR_I", nominal=3.0, index=1,
            method="SCANNER_2400DPI", procedure=None, value=3.041, **over):
    if procedure is None:
        procedure = ("PIPELINE_ESTIMATOR_ON_SCAN" if method.startswith("SCANNER")
                     else "MANUAL_VISUAL_CROSSHAIR")
    row = {
        "glyph_id": vrt.canonical_glyph_id(panel, shape, nominal, index),
        "panel_id": panel, "glyph_shape": shape, "nominal_h_mm": nominal,
        "glyph_index": index, "method": method,
        "measurement_procedure": procedure,
        "reference_h_mm": value, "unit": "mm", "reference_u_mm": 0.01,
        "instrument_id": "INST-1", "instrument_cal_ref": "CAL-1",
        "operator": "OP1", "measured_at": "2026-01-01T00:00:00Z",
        "n_repeats": 1, "raw_readings": "", "cross_check_status": "PENDING",
        "notes": "",
    }
    row.update(over)
    return row


def write_table(path, rows, fields=None):
    fields = fields or list(vrt.REQUIRED_FIELDS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({f: r.get(f, "") for f in fields})
    return path


def codes(issues, severity=None):
    return sorted(i["code"] for i in issues
                  if severity is None or i["severity"] == severity)


class TestSchema(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _validate(self, rows, fields=None, manifest=None):
        p = write_table(os.path.join(self.tmp, "reference_table.csv"), rows, fields)
        return vrt.validate(vrt.load_table(p), manifest)

    def test_minimal_valid_pair_is_accepted(self):
        rows = [ref_row(), ref_row(method="MICROSCOPE", value=3.052)]
        issues, summary = self._validate(rows)
        self.assertEqual(codes(issues, vrt.ERROR), [])
        self.assertEqual(summary["glyphs"], 1)
        self.assertEqual(summary["glyphs_cross_checked"], 1)

    def test_missing_required_field_is_refused(self):
        fields = [f for f in vrt.REQUIRED_FIELDS if f != "unit"]
        p = write_table(os.path.join(self.tmp, "reference_table.csv"),
                        [ref_row()], fields)
        with self.assertRaises(vrt.ReferenceTableError):
            vrt.load_table(p)

    def test_empty_table_is_refused(self):
        p = write_table(os.path.join(self.tmp, "reference_table.csv"), [])
        with self.assertRaises(vrt.ReferenceTableError):
            vrt.load_table(p)

    def test_unit_must_be_mm(self):
        issues, _ = self._validate([ref_row(unit="um")])
        self.assertIn("BAD_UNIT", codes(issues, vrt.ERROR))

    def test_missing_reference_value_is_an_error_not_zero(self):
        issues, _ = self._validate([ref_row(reference_h_mm="")])
        self.assertIn("MISSING_REFERENCE_VALUE", codes(issues, vrt.ERROR))

    def test_nonpositive_reference_value_rejected(self):
        issues, _ = self._validate([ref_row(reference_h_mm=-1.0)])
        self.assertIn("NONPOSITIVE_REFERENCE_VALUE", codes(issues, vrt.ERROR))

    def test_missing_uncertainty_warns_but_does_not_fail(self):
        issues, _ = self._validate([ref_row(reference_u_mm="")])
        self.assertIn("NO_REFERENCE_UNCERTAINTY", codes(issues, vrt.WARN))
        self.assertNotIn("BAD_REFERENCE_UNCERTAINTY", codes(issues, vrt.ERROR))

    def test_bad_method_and_procedure_enumerations(self):
        issues, _ = self._validate([ref_row(method="RULER",
                                            procedure="EYEBALL")])
        self.assertIn("BAD_METHOD", codes(issues, vrt.ERROR))
        self.assertIn("BAD_PROCEDURE", codes(issues, vrt.ERROR))

    def test_unresolved_procedure_cannot_serve_as_reference(self):
        issues, _ = self._validate([ref_row(procedure="UNRESOLVED")])
        self.assertIn("PROCEDURE_UNRESOLVED", codes(issues, vrt.ERROR))

    def test_glyph_id_must_match_canonical_form(self):
        issues, _ = self._validate([ref_row(glyph_id="whatever")])
        self.assertIn("GLYPH_ID_MISMATCH", codes(issues, vrt.ERROR))

    def test_canonical_glyph_id_is_stable_and_deterministic(self):
        a = vrt.canonical_glyph_id("P01", "BAR_I", 3.0, 1)
        b = vrt.canonical_glyph_id("P01", "BAR_I", 3.00, 1.0)
        self.assertEqual(a, b)
        self.assertEqual(a, "P01:BAR_I:3.00:1")

    def test_missing_provenance_is_an_error(self):
        issues, _ = self._validate([ref_row(operator="", measured_at="")])
        self.assertIn("MISSING_PROVENANCE", codes(issues, vrt.ERROR))

    def test_missing_calibration_reference_warns(self):
        issues, _ = self._validate([ref_row(instrument_cal_ref="")])
        self.assertIn("NO_INSTRUMENT_CALIBRATION_REF", codes(issues, vrt.WARN))

    def test_reference_equal_to_nominal_is_flagged(self):
        # the frozen prohibition: nominal artwork height is never ground truth
        issues, _ = self._validate([ref_row(reference_h_mm=3.0, nominal_h_mm=3.0)])
        self.assertIn("REFERENCE_EQUALS_NOMINAL", codes(issues, vrt.WARN))


class TestDuplicatesAndSupersession(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _validate(self, rows):
        p = write_table(os.path.join(self.tmp, "reference_table.csv"), rows)
        return vrt.validate(vrt.load_table(p), None)

    def test_exact_duplicate_is_an_error(self):
        issues, _ = self._validate([ref_row(), ref_row()])
        self.assertIn("DUPLICATE_ROW", codes(issues, vrt.ERROR))

    def test_remeasurement_is_supersession_not_duplication(self):
        issues, summary = self._validate([
            ref_row(measured_at="2026-01-01T00:00:00Z", value=3.041),
            ref_row(measured_at="2026-01-02T00:00:00Z", value=3.044)])
        self.assertNotIn("DUPLICATE_ROW", codes(issues, vrt.ERROR))
        self.assertIn("SUPERSEDED_ROWS", codes(issues, vrt.INFO))
        self.assertEqual(summary["superseded_rows"], 1)

    def test_distinct_glyphs_are_not_duplicates(self):
        issues, summary = self._validate([
            ref_row(shape="BAR_I"), ref_row(shape="RING_O")])
        self.assertEqual(codes(issues, vrt.ERROR), [])
        self.assertEqual(summary["glyphs"], 2)


class TestIndependence(unittest.TestCase):
    """The core B2 protection: a cross-check pair must not be all-pipeline."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _validate(self, rows):
        p = write_table(os.path.join(self.tmp, "reference_table.csv"), rows)
        return vrt.validate(vrt.load_table(p), None)

    def test_microscope_may_not_use_the_pipeline_estimator(self):
        issues, _ = self._validate([
            ref_row(method="MICROSCOPE", procedure="PIPELINE_ESTIMATOR_ON_SCAN")])
        self.assertIn("MICROSCOPE_NOT_INDEPENDENT", codes(issues, vrt.ERROR))

    def test_all_pipeline_pair_cannot_support_p1(self):
        issues, summary = self._validate([
            ref_row(method="SCANNER_2400DPI", procedure="PIPELINE_ESTIMATOR_ON_SCAN"),
            ref_row(method="MICROSCOPE", procedure="PIPELINE_ESTIMATOR_ON_SCAN",
                    value=3.05)])
        self.assertIn("PAIR_NOT_INDEPENDENT", codes(issues, vrt.ERROR))
        self.assertEqual(summary["glyphs_cross_checked_pipeline_only"], 1)

    def test_mixed_procedure_pair_is_independent_enough(self):
        issues, summary = self._validate([
            ref_row(method="SCANNER_2400DPI", procedure="PIPELINE_ESTIMATOR_ON_SCAN"),
            ref_row(method="MICROSCOPE", procedure="MANUAL_VISUAL_CROSSHAIR",
                    value=3.05)])
        self.assertEqual(codes(issues, vrt.ERROR), [])
        self.assertEqual(summary["glyphs_cross_checked_pipeline_only"], 0)


class TestDisagreementRecording(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _validate(self, rows):
        p = write_table(os.path.join(self.tmp, "reference_table.csv"), rows)
        return vrt.validate(vrt.load_table(p), None)

    def test_bad_cross_check_status_rejected(self):
        issues, _ = self._validate([ref_row(cross_check_status="MAYBE")])
        self.assertIn("BAD_CROSS_CHECK_STATUS", codes(issues, vrt.ERROR))

    def test_disagreement_must_carry_a_note(self):
        issues, _ = self._validate([ref_row(cross_check_status="DISAGREED",
                                            notes="")])
        self.assertIn("DISAGREEMENT_WITHOUT_NOTE", codes(issues, vrt.ERROR))

    def test_unusable_must_carry_a_note(self):
        issues, _ = self._validate([ref_row(cross_check_status="UNUSABLE",
                                            notes="")])
        self.assertIn("DISAGREEMENT_WITHOUT_NOTE", codes(issues, vrt.ERROR))

    def test_documented_disagreement_is_accepted_and_counted(self):
        issues, summary = self._validate([
            ref_row(cross_check_status="DISAGREED",
                    notes="scanner 3.041 vs microscope 3.128; re-measure scheduled")])
        self.assertEqual(codes(issues, vrt.ERROR), [])
        self.assertEqual(summary["cross_check_status_counts"]["DISAGREED"], 1)


class TestProvenanceLinkage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _validate(self, rows, manifest):
        p = write_table(os.path.join(self.tmp, "reference_table.csv"), rows)
        return vrt.validate(vrt.load_table(p), manifest)

    def test_run_without_reference_is_reported(self):
        manifest = {"runs": [{"run_id": "P09-A-OP1-R1", "panel_id": "P09",
                              "glyph_label": "BAR_I", "nominal_h_mm": 3.0,
                              "safety_class": "SAFE"}]}
        issues, summary = self._validate([ref_row()], manifest)
        self.assertIn("NO_REFERENCE_FOR_RUN", codes(issues, vrt.ERROR))
        self.assertEqual(summary["manifest_glyphs_without_reference"], 1)

    def test_matching_run_links_cleanly(self):
        manifest = {"runs": [{"run_id": "P01-A-OP1-R1", "panel_id": "P01",
                              "glyph_label": "BAR_I", "nominal_h_mm": 3.0,
                              "safety_class": "SAFE"}]}
        issues, summary = self._validate(
            [ref_row(), ref_row(method="MICROSCOPE", value=3.05)], manifest)
        self.assertEqual(codes(issues, vrt.ERROR), [])
        self.assertEqual(summary["manifest_glyphs_without_reference"], 0)

    def test_stress_runs_do_not_require_a_reference(self):
        manifest = {"runs": [{"run_id": "P09-A-OP1-GLARE-S01", "panel_id": "P09",
                              "glyph_label": "BAR_I", "nominal_h_mm": 3.0,
                              "safety_class": "UNSAFE_DETECTABLE"}]}
        issues, summary = self._validate([ref_row()], manifest)
        self.assertNotIn("NO_REFERENCE_FOR_RUN", codes(issues, vrt.ERROR))
        self.assertEqual(summary["manifest_glyphs_needing_reference"], 0)

    def test_orphan_reference_panel_warns(self):
        manifest = {"runs": [{"run_id": "P02-A-OP1-R1", "panel_id": "P02",
                              "glyph_label": "BAR_I", "nominal_h_mm": 3.0,
                              "safety_class": "SAFE"}]}
        issues, _ = self._validate([ref_row(panel="P01")], manifest)
        self.assertIn("REFERENCE_PANEL_NOT_IN_MANIFEST", codes(issues, vrt.WARN))


class TestDeterminismAndStandin(unittest.TestCase):
    def test_validation_is_deterministic(self):
        rows = vrt.load_table(STANDIN_TABLE)
        a_issues, a_summary = vrt.validate(rows, None)
        b_issues, b_summary = vrt.validate(rows, None)
        self.assertEqual(a_issues, b_issues)
        self.assertEqual(a_summary, b_summary)

    def test_standin_table_satisfies_the_schema(self):
        # the stand-in is labelled NOT PHYSICAL EVIDENCE; this only checks plumbing
        issues, summary = vrt.validate(vrt.load_table(STANDIN_TABLE), None)
        self.assertEqual(codes(issues, vrt.ERROR), [])
        self.assertEqual(summary["glyphs_cross_checked_pipeline_only"], 0)
        self.assertGreater(summary["glyphs_cross_checked"], 0)

    def test_agreement_uses_the_frozen_criteria_source(self):
        rep = vrt.agreement_report(STANDIN_TABLE)
        self.assertEqual(rep["P1"]["threshold_reference"]["document"],
                         "docs/P0_CRITERIA.md")
        self.assertIn("mean_abs_difference_mm", rep["P1"]["statistics"])

    def test_cli_accepts_standin_and_rejects_broken_table(self):
        self.assertEqual(vrt.main(["--table", STANDIN_TABLE]), 0)
        tmp = tempfile.mkdtemp()
        try:
            p = write_table(os.path.join(tmp, "reference_table.csv"),
                            [ref_row(unit="inch")])
            self.assertEqual(vrt.main(["--table", p]), 1)
            self.assertEqual(vrt.main(["--table", os.path.join(tmp, "nope.csv")]), 2)
        finally:
            shutil.rmtree(tmp)


def m1_raw(h_mm, band=0.030, spread=0.017320, repeats=(-1, 0, 1)):
    """Build `Obot/Ibot/Itop/Otop` readings whose bisected mean is exactly h_mm."""
    half = band / 2.0
    out = []
    for k in repeats:
        h = h_mm + k * spread
        out.append("%.6f/%.6f/%.6f/%.6f" % (-half, +half, h - half, h + half))
    return ";".join(out)


def m1_row(value=3.052, **over):
    row = dict(method="MICROSCOPE", value=value, operator="OP2",
               n_repeats=3, raw_readings=m1_raw(value))
    row.update(over)
    return ref_row(**row)


class TestM1Auditability(unittest.TestCase):
    """M1 = the frozen microscope transition-band bisection (§4.1).

    These tests check that a recorded microscope value can be re-derived from its own
    raw readings.  They assert nothing about physical accuracy.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _validate(self, rows):
        p = write_table(os.path.join(self.tmp, "reference_table.csv"), rows)
        return vrt.validate(vrt.load_table(p), None)

    # --- the bisection rule itself ------------------------------------------
    def test_bisection_is_the_midpoint_of_each_transition_band(self):
        heights, mean = vrt.parse_m1_readings("-0.015/0.015/2.985/3.015")
        self.assertEqual(len(heights), 1)
        self.assertAlmostEqual(heights[0], 3.0, places=9)
        self.assertAlmostEqual(mean, 3.0, places=9)

    def test_bisection_is_invariant_to_the_band_width(self):
        """The whole point of M1: a symmetric band gives the same height."""
        narrow = vrt.parse_m1_readings(m1_raw(3.0, band=0.004, repeats=(0,)))[1]
        wide = vrt.parse_m1_readings(m1_raw(3.0, band=0.120, repeats=(0,)))[1]
        self.assertAlmostEqual(narrow, wide, places=9)
        self.assertAlmostEqual(wide, 3.0, places=9)

    def test_symmetric_repeats_average_to_the_recorded_value(self):
        _h, mean = vrt.parse_m1_readings(m1_raw(2.028))
        self.assertAlmostEqual(mean, 2.028, places=9)

    def test_unparseable_readings_raise(self):
        for bad in ("", "  ", "1/2/3", "a/b/c/d", "1/2/3/4/5"):
            with self.assertRaises(ValueError):
                vrt.parse_m1_readings(bad)

    # --- validator behaviour ------------------------------------------------
    def test_compliant_microscope_row_is_clean(self):
        issues, _s = self._validate([ref_row(), m1_row()])
        self.assertEqual(codes(issues, "ERROR"), [])
        self.assertEqual(codes(issues, "WARN"), [])

    def test_missing_raw_readings_warns_but_does_not_reject(self):
        issues, _s = self._validate([ref_row(), m1_row(raw_readings="")])
        self.assertIn("MICROSCOPE_WITHOUT_RAW_READINGS", codes(issues, "WARN"))
        self.assertEqual(codes(issues, "ERROR"), [])

    def test_too_few_repeats_warns(self):
        issues, _s = self._validate(
            [ref_row(), m1_row(n_repeats=1, raw_readings=m1_raw(3.052, repeats=(0,)))])
        self.assertIn("MICROSCOPE_REPEATS_BELOW_M1", codes(issues, "WARN"))
        self.assertEqual(codes(issues, "ERROR"), [])

    def test_unparseable_raw_readings_warn(self):
        issues, _s = self._validate([ref_row(), m1_row(raw_readings="3.05,3.06")])
        self.assertIn("RAW_READINGS_UNPARSEABLE", codes(issues, "WARN"))

    def test_readings_that_do_not_reproduce_the_value_are_an_error(self):
        issues, _s = self._validate([ref_row(), m1_row(raw_readings=m1_raw(3.200))])
        self.assertIn("RAW_READINGS_INCONSISTENT", codes(issues, "ERROR"))

    def test_rounding_scale_disagreement_is_tolerated(self):
        issues, _s = self._validate(
            [ref_row(), m1_row(raw_readings=m1_raw(3.052 + 2e-6))])
        self.assertNotIn("RAW_READINGS_INCONSISTENT", codes(issues, "ERROR"))

    def test_n_repeats_must_match_the_readings(self):
        issues, _s = self._validate([ref_row(), m1_row(n_repeats=5)])
        self.assertIn("N_REPEATS_MISMATCH", codes(issues, "ERROR"))

    def test_m1_checks_do_not_apply_to_scanner_rows(self):
        issues, _s = self._validate([ref_row(n_repeats=1, raw_readings=""), m1_row()])
        self.assertNotIn("MICROSCOPE_WITHOUT_RAW_READINGS", codes(issues, "WARN"))
        self.assertNotIn("MICROSCOPE_REPEATS_BELOW_M1", codes(issues, "WARN"))

    # --- observer independence (rule R6) ------------------------------------
    def test_shared_operator_across_methods_warns(self):
        issues, _s = self._validate([ref_row(operator="OP1"),
                                     m1_row(operator="OP1")])
        self.assertIn("SAME_OPERATOR_BOTH_METHODS", codes(issues, "WARN"))
        self.assertEqual(codes(issues, "ERROR"), [])

    def test_distinct_operators_do_not_warn(self):
        issues, _s = self._validate([ref_row(operator="OP1"),
                                     m1_row(operator="OP2")])
        self.assertNotIn("SAME_OPERATOR_BOTH_METHODS", codes(issues, "WARN"))

    def test_standin_microscope_rows_are_m1_compliant(self):
        issues, summary = vrt.validate(vrt.load_table(STANDIN_TABLE), None)
        self.assertEqual(codes(issues, "ERROR"), [])
        self.assertEqual(codes(issues, "WARN"), [])
        self.assertEqual(summary["rows_by_method"]["MICROSCOPE"], 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
