"""Tests for the B2 pre-capture setup gate.

These test the **gate logic only**.  No test here asserts that any instrument
exists, and no test produces a measurement.  The `satisfied()` helper is a
hypothetical fully-equipped setup used to prove the gate is *reachable* — the
mistake the P7 memo caught was a criterion that could never be satisfied, so a
gate that can only ever say NO is a bug, not a safety feature.
"""
from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import verify_b2_setup as vbs                     # noqa: E402

from p0.core import dump_json                     # noqa: E402


def satisfied():
    """A hypothetical fully-verified setup.  Not a claim that it exists."""
    return {
        "recorded_by": "OP1", "recorded_at": "2026-01-01T00:00:00Z",
        "scanner": {
            "instrument_id": "SCAN-LAB-01", "optical_dpi": 2400,
            "dpi_is_optical": True, "dpi_used_for_scan": 2400,
            "scan_mode": "GREYSCALE", "bit_depth": 8,
            "enhancement_off": True,
            "enhancement_items_disabled": ["sharpening", "descreen", "auto tone"],
            "output_format": "TIFF", "resampling_or_rescaling": False,
            "single_session_all_panels": True,
            "scale_calibration_ref": "SCAL-2026-01-01-A",
            "scale_factor_x": 1.0002, "scale_factor_y": 1.0006,
            "platen_nonuniformity_recorded": True, "frame_in_scan": False,
        },
        "length_standard": {
            "standard_id": "GRAT-77", "type": "GLASS_GRATICULE",
            "certificate_ref": "CERT-GRAT-77-2025", "certificate_issued": "2025-06-01",
            "certificate_expires": "2027-06-01",
            "traceability": "as stated on the certificate",
            "stated_uncertainty_mm": 0.002, "both_axes_verified": True,
        },
        "microscope": {
            "instrument_id": "TMS-03", "type": "TOOLMAKERS_MICROSCOPE",
            "has_xy_stage_with_readout": True, "stage_rotation_available": True,
            "reading_resolution_mm": 0.001, "calibration_ref": "CERT-TMS-03-2025",
            "illumination_mode": "REFLECTED", "m1_procedure_read": True,
            "m1_checklist_available": True, "operator_trained_against_m1": True,
            "inter_operator_check_done": True, "repeats_planned": 3,
            "raw_reading_format": "Obot/Ibot/Itop/Otop",
        },
        "caliper": {
            "instrument_id": "CAL-11", "resolution_mm": 0.01,
            "calibration_record_ref": "CERT-CAL-11-2025",
            "used_for_glyph_reference": False,
        },
        "printing": {
            "printer_id": "LJ-1", "scale_verified_against_100mm_bar": True,
            "measured_check_bar_mm": 100.05, "coupon_panels_printed": 20,
            "stock_description": "matte 200 gsm", "stock_dimensionally_stable": True,
            "real_packaged_products_used_as_p0_sample": False,
        },
        "operators": {
            "scanner_operator": "OP1", "microscope_operator": "OP2",
            "microscope_blind_to_scanner_values": True,
        },
        "software": {
            "scan_measurement_tool": "tools/measure_scan.py@abc1234",
            "scan_measurement_dry_run_passed": True,
            "png_conversion_verified_no_sharpening": True,
            "reference_validator_run_clean": True,
            "reference_table_committed_before_capture": True,
        },
        "open_decisions": dict(
            [(k, "RESOLVED: see decision log") for k in vbs.OPEN_DECISION_KEYS]
        ),
    }


def verdict(ev):
    _results, summary = vbs.verify(ev)
    return summary["verified"]


def failed_codes(ev):
    results, _summary = vbs.verify(ev)
    return sorted(r["code"] for r in results
                  if r["level"] == vbs.MANDATORY and not r["passed"])


class TestGateReachability(unittest.TestCase):
    def test_a_fully_verified_setup_returns_yes(self):
        """The gate must be satisfiable, or it is not a gate."""
        self.assertTrue(verdict(satisfied()))

    def test_blank_template_returns_no(self):
        self.assertFalse(verdict(vbs.template()))

    def test_blank_template_fails_every_mandatory_check(self):
        results, summary = vbs.verify(vbs.template())
        n_mandatory = sum(1 for r in results if r["level"] == vbs.MANDATORY)
        self.assertEqual(summary["mandatory_failed"], n_mandatory)

    def test_empty_object_returns_no_and_does_not_crash(self):
        self.assertFalse(verdict({}))

    def test_verification_is_deterministic(self):
        a = vbs.verify(satisfied())
        b = vbs.verify(satisfied())
        self.assertEqual(a, b)

    def test_advisories_alone_do_not_block(self):
        ev = satisfied()
        ev["operators"]["microscope_operator"] = "OP1"        # R6(c) is a should
        ev["microscope"]["inter_operator_check_done"] = False
        results, summary = vbs.verify(ev)
        self.assertTrue(summary["verified"])
        self.assertTrue(any(r["level"] == vbs.ADVISORY and not r["passed"]
                            for r in results))


class TestNoSilentAssumptions(unittest.TestCase):
    def test_placeholders_are_not_evidence(self):
        for bad in ("", "  ", "TBD", "tbd", "N/A", "unknown", "UNSPECIFIED",
                    "pending", "-", "?", "None", "null"):
            self.assertFalse(vbs.named(bad), bad)
        self.assertTrue(vbs.named("SCAN-LAB-01"))

    def test_placeholder_instrument_id_fails(self):
        for bad in ("TBD", "UNSPECIFIED", "", None):
            ev = satisfied()
            ev["scanner"]["instrument_id"] = bad
            self.assertIn("SCANNER_IDENTIFIED", failed_codes(ev))

    def test_a_string_is_not_a_boolean(self):
        ev = satisfied()
        ev["scanner"]["dpi_is_optical"] = "yes"
        self.assertIn("SCANNER_DPI_IS_OPTICAL", failed_codes(ev))

    def test_missing_section_fails_that_group_only(self):
        ev = satisfied()
        del ev["microscope"]
        codes = failed_codes(ev)
        self.assertIn("MICROSCOPE_IDENTIFIED", codes)
        self.assertNotIn("SCANNER_IDENTIFIED", codes)

    def test_null_boolean_is_not_false(self):
        """`frame_in_scan` must be explicitly false, not merely absent."""
        ev = satisfied()
        ev["scanner"]["frame_in_scan"] = None
        self.assertIn("SCANNER_NO_FRAME_IN_SCAN", failed_codes(ev))


class TestScannerChecks(unittest.TestCase):
    def test_sub_2400_optical_dpi_fails(self):
        for dpi in (300, 600, 1200, 2399):
            ev = satisfied()
            ev["scanner"]["optical_dpi"] = dpi
            ev["scanner"]["dpi_used_for_scan"] = dpi
            self.assertIn("SCANNER_OPTICAL_DPI", failed_codes(ev), dpi)

    def test_higher_optical_dpi_passes(self):
        ev = satisfied()
        ev["scanner"]["optical_dpi"] = 4800
        ev["scanner"]["dpi_used_for_scan"] = 4800
        self.assertTrue(verdict(ev))

    def test_scanning_below_the_optical_capability_fails(self):
        ev = satisfied()
        ev["scanner"]["dpi_used_for_scan"] = 1200
        self.assertIn("SCANNER_SCANNED_AT_REQUIRED_DPI", failed_codes(ev))

    def test_jpeg_output_fails(self):
        for fmt in ("JPEG", "jpg", "JPG"):
            ev = satisfied()
            ev["scanner"]["output_format"] = fmt
            self.assertIn("SCANNER_LOSSLESS_OUTPUT", failed_codes(ev), fmt)

    def test_enhancement_off_must_name_what_was_disabled(self):
        ev = satisfied()
        ev["scanner"]["enhancement_items_disabled"] = []
        self.assertIn("SCANNER_ENHANCEMENT_OFF", failed_codes(ev))

    def test_frame_in_the_scan_fails_because_s3_is_no(self):
        ev = satisfied()
        ev["scanner"]["frame_in_scan"] = True
        self.assertIn("SCANNER_NO_FRAME_IN_SCAN", failed_codes(ev))

    def test_one_axis_calibration_fails(self):
        ev = satisfied()
        ev["scanner"]["scale_factor_y"] = None
        self.assertIn("SCANNER_BOTH_AXES_CALIBRATED", failed_codes(ev))

    def test_multi_session_scanning_fails(self):
        ev = satisfied()
        ev["scanner"]["single_session_all_panels"] = False
        self.assertIn("SCANNER_SINGLE_SESSION", failed_codes(ev))

    def test_platen_nonuniformity_must_be_recorded(self):
        ev = satisfied()
        ev["scanner"]["platen_nonuniformity_recorded"] = False
        self.assertIn("SCANNER_PLATEN_NONUNIFORMITY_RECORDED", failed_codes(ev))


class TestStandardChecks(unittest.TestCase):
    def test_missing_certificate_fails(self):
        ev = satisfied()
        ev["length_standard"]["certificate_ref"] = None
        self.assertIn("STANDARD_CERTIFICATE_REF", failed_codes(ev))

    def test_unknown_standard_type_fails(self):
        ev = satisfied()
        ev["length_standard"]["type"] = "PLASTIC_RULER"
        self.assertIn("STANDARD_TYPE", failed_codes(ev))

    def test_coarse_standard_is_advisory_not_fatal(self):
        ev = satisfied()
        ev["length_standard"]["stated_uncertainty_mm"] = 0.05
        results, summary = vbs.verify(ev)
        self.assertTrue(summary["verified"])
        self.assertIn("STANDARD_UNCERTAINTY_VS_TARGET",
                      [r["code"] for r in results
                       if r["level"] == vbs.ADVISORY and not r["passed"]])


class TestMicroscopeChecks(unittest.TestCase):
    def test_viewer_without_a_measuring_stage_fails(self):
        ev = satisfied()
        ev["microscope"]["has_xy_stage_with_readout"] = False
        self.assertIn("MICROSCOPE_XY_STAGE_READOUT", failed_codes(ev))

    def test_high_resolution_claim_without_a_number_fails(self):
        """An instrument is not acceptable because it sounds high-resolution."""
        ev = satisfied()
        ev["microscope"]["reading_resolution_mm"] = "very high"
        self.assertIn("MICROSCOPE_READING_RESOLUTION", failed_codes(ev))

    def test_transmitted_illumination_fails(self):
        ev = satisfied()
        ev["microscope"]["illumination_mode"] = "TRANSMITTED"
        self.assertIn("MICROSCOPE_REFLECTED_ILLUMINATION", failed_codes(ev))

    def test_untrained_operator_fails(self):
        ev = satisfied()
        ev["microscope"]["operator_trained_against_m1"] = False
        self.assertIn("MICROSCOPE_OPERATOR_TRAINED", failed_codes(ev))

    def test_fewer_than_three_repeats_fails(self):
        ev = satisfied()
        ev["microscope"]["repeats_planned"] = 2
        self.assertIn("MICROSCOPE_REPEATS_PLANNED", failed_codes(ev))

    def test_wrong_raw_format_fails(self):
        ev = satisfied()
        ev["microscope"]["raw_reading_format"] = "height only"
        self.assertIn("MICROSCOPE_RAW_FORMAT", failed_codes(ev))

    def test_usb_microscope_passes_but_is_flagged_secondary(self):
        ev = satisfied()
        ev["microscope"]["type"] = "USB_MICROSCOPE_WITH_CALIBRATION_SLIDE"
        results, summary = vbs.verify(ev)
        self.assertTrue(summary["verified"])
        self.assertIn("MICROSCOPE_IS_PREFERRED_CLASS",
                      [r["code"] for r in results
                       if r["level"] == vbs.ADVISORY and not r["passed"]])

    def test_coarse_reading_step_is_reported_against_the_p1_band(self):
        ev = satisfied()
        ev["microscope"]["reading_resolution_mm"] = 0.05
        results, summary = vbs.verify(ev)
        self.assertTrue(summary["verified"])          # no invented limit
        bad = [r for r in results if r["code"] == "MICROSCOPE_QUANTISATION_SHARE_OF_P1"]
        self.assertEqual(len(bad), 1)
        self.assertFalse(bad[0]["passed"])
        self.assertEqual(bad[0]["level"], vbs.ADVISORY)


class TestOtherGroups(unittest.TestCase):
    def test_caliper_used_as_glyph_reference_fails(self):
        ev = satisfied()
        ev["caliper"]["used_for_glyph_reference"] = True
        self.assertIn("CALIPER_NOT_USED_AS_GLYPH_REFERENCE", failed_codes(ev))

    def test_print_scale_beyond_one_percent_fails(self):
        for bar in (98.9, 101.2):
            ev = satisfied()
            ev["printing"]["measured_check_bar_mm"] = bar
            self.assertIn("PRINT_SCALE_WITHIN_TOLERANCE", failed_codes(ev), bar)

    def test_print_scale_within_one_percent_passes(self):
        for bar in (99.1, 100.0, 100.9):
            ev = satisfied()
            ev["printing"]["measured_check_bar_mm"] = bar
            self.assertTrue(verdict(ev), bar)

    def test_fewer_panels_than_the_frozen_design_fails(self):
        ev = satisfied()
        ev["printing"]["coupon_panels_printed"] = 4
        self.assertIn("COUPON_PANELS_PRINTED", failed_codes(ev))

    def test_real_products_as_sample_is_advisory_flagged(self):
        ev = satisfied()
        ev["printing"]["real_packaged_products_used_as_p0_sample"] = True
        results, _s = vbs.verify(ev)
        self.assertIn("REAL_PRODUCTS_NOT_USED_AS_SAMPLE",
                      [r["code"] for r in results
                       if r["level"] == vbs.ADVISORY and not r["passed"]])

    def test_unblinded_microscope_operator_fails(self):
        ev = satisfied()
        ev["operators"]["microscope_blind_to_scanner_values"] = False
        self.assertIn("MICROSCOPE_BLIND_TO_SCANNER_VALUES", failed_codes(ev))

    def test_missing_scan_measurement_tool_fails(self):
        ev = satisfied()
        ev["software"]["scan_measurement_tool"] = None
        self.assertIn("SCAN_MEASUREMENT_TOOL_EXISTS", failed_codes(ev))

    def test_no_dry_run_fails(self):
        ev = satisfied()
        ev["software"]["scan_measurement_dry_run_passed"] = False
        self.assertIn("SCAN_MEASUREMENT_DRY_RUN", failed_codes(ev))


class TestOpenDecisions(unittest.TestCase):
    def test_every_open_decision_must_be_resolved(self):
        for key in vbs.OPEN_DECISION_KEYS:
            ev = satisfied()
            ev["open_decisions"][key] = None
            self.assertIn("DECISION_" + key.upper(), failed_codes(ev), key)

    def test_a_non_resolved_answer_does_not_count(self):
        ev = satisfied()
        ev["open_decisions"]["S4_platen_rule"] = "probably fine"
        self.assertIn("DECISION_S4_PLATEN_RULE", failed_codes(ev))

    def test_settled_decisions_are_carried_in_the_template(self):
        tpl = vbs.template()
        for key, val in vbs.SETTLED_DECISIONS.items():
            self.assertTrue(val.startswith("RESOLVED"))
            self.assertEqual(tpl["open_decisions"][key], val)

    def test_settled_and_open_keys_do_not_overlap(self):
        self.assertEqual(set(vbs.SETTLED_DECISIONS) & set(vbs.OPEN_DECISION_KEYS),
                         set())


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_template_then_verify_returns_not_verified(self):
        p = os.path.join(self.tmp, "b2_setup.json")
        self.assertEqual(vbs.main(["--template", p]), 0)
        self.assertTrue(os.path.exists(p))
        buf, old = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            rc = vbs.main(["--evidence", p])
        finally:
            sys.stdout = old
        self.assertEqual(rc, 1)
        self.assertIn("B2_SETUP_VERIFIED = NO", buf.getvalue())

    def test_satisfied_evidence_exits_zero(self):
        p = os.path.join(self.tmp, "ok.json")
        dump_json(p, satisfied())
        buf, old = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            rc = vbs.main(["--evidence", p])
        finally:
            sys.stdout = old
        self.assertEqual(rc, 0)
        self.assertIn("B2_SETUP_VERIFIED = YES", buf.getvalue())

    def test_missing_file_exits_two(self):
        buf, old = io.StringIO(), sys.stderr
        sys.stderr = buf
        try:
            rc = vbs.main(["--evidence", os.path.join(self.tmp, "nope.json")])
        finally:
            sys.stderr = old
        self.assertEqual(rc, 2)
        self.assertIn("B2_SETUP_VERIFIED = NO", buf.getvalue())

    def test_json_out_records_the_verdict(self):
        from p0.core import load_json
        p = os.path.join(self.tmp, "ok.json")
        out = os.path.join(self.tmp, "result.json")
        dump_json(p, satisfied())
        buf, old = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            vbs.main(["--evidence", p, "--json-out", out])
        finally:
            sys.stdout = old
        got = load_json(out)
        self.assertEqual(got["B2_SETUP_VERIFIED"], "YES")
        self.assertTrue(got["summary"]["verified"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
