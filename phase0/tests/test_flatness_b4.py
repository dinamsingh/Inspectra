"""Tests for the B4 pre-capture flatness acceptance.

These test the **acceptance and evidence logic only**.  No test asserts that any
panel is flat, none uses physical data, and none measures anything: the register is
built inline.  `passing_panel()` is a hypothetical surveyed panel, used to prove the
acceptance is reachable — a rule that can only ever say NO would be a bug, not a
safety feature.
"""
from __future__ import annotations

import io
import math
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import validate_flatness as vf                    # noqa: E402

from p0.core import dump_json, load_json          # noqa: E402

MODEL = os.path.join(ROOT, "config", "uncertainty_model_v1.json")


def bound():
    return vf.model_bound_deg()


def passing_panel(**over):
    rec = {
        "backing_id": "PLATE-01", "backing_rigid_flat_verified": True,
        "mounting_method": "CLAMPED",
        "instrument": "feeler gauge set 0.03-1.00 mm",
        "instrument_resolution_mm": 0.03,
        "straightedge_span_long_mm": 50.0, "max_gap_long_mm": 0.09,
        "straightedge_span_short_mm": 20.0, "max_gap_short_mm": 0.06,
        "frame_flush_check": vf.FLUSH_OK,
        "operator": "OP1", "measured_at": "2026-01-01T00:00:00Z",
        "status": "PASS", "notes": "",
    }
    rec.update(over)
    return rec


def register(panels=None, **over):
    reg = {
        "acceptance": {"max_local_tilt_deg": bound(),
                       "source": vf.ACCEPTANCE_SOURCE},
        "panels": panels if panels is not None else {"P01": passing_panel()},
    }
    reg.update(over)
    return reg


def codes(issues, severity="ERROR"):
    return sorted(i["code"] for i in issues if i["severity"] == severity)


def verdict(reg, manifest=None):
    _i, summary, _p = vf.validate(reg, manifest)
    return summary["verified"]


def statuses(reg, manifest=None):
    _i, _s, panels = vf.validate(reg, manifest)
    return {k: v["derived_status"] for k, v in panels.items()}


# ---------------------------------------------------------------------------
# the acceptance comes from the model, not from this tool
# ---------------------------------------------------------------------------

class TestAcceptanceProvenance(unittest.TestCase):
    def test_acceptance_is_read_from_the_uncertainty_model(self):
        self.assertAlmostEqual(bound(),
                               load_json(MODEL)["residual_tilt_bound_deg"])

    def test_a_loosened_acceptance_is_rejected(self):
        """Relaxing the mechanical rule would invalidate every emitted interval."""
        for stated in (5.0, 10.0, 3.5):
            reg = register()
            reg["acceptance"]["max_local_tilt_deg"] = stated
            issues, _s, _p = vf.validate(reg)
            self.assertIn("ACCEPTANCE_NOT_FROM_MODEL", codes(issues), stated)

    def test_a_tightened_acceptance_is_also_rejected(self):
        """The register mirrors the model; it does not get to redefine it."""
        reg = register()
        reg["acceptance"]["max_local_tilt_deg"] = 1.0
        issues, _s, _p = vf.validate(reg)
        self.assertIn("ACCEPTANCE_NOT_FROM_MODEL", codes(issues))

    def test_missing_acceptance_block_is_rejected(self):
        reg = register()
        del reg["acceptance"]
        issues, _s, _p = vf.validate(reg)
        self.assertIn("ACCEPTANCE_MISSING", codes(issues))

    def test_summary_reports_the_derived_gap_limits(self):
        _i, summary, _p = vf.validate(register())
        self.assertAlmostEqual(summary["max_gap_long_mm"],
                               math.tan(math.radians(bound())) * 50.0 / 4.0,
                               places=6)
        self.assertAlmostEqual(summary["max_gap_short_mm"],
                               math.tan(math.radians(bound())) * 20.0 / 4.0,
                               places=6)


class TestPhysicsMatchesTheRepository(unittest.TestCase):
    """The closed form must reproduce what out/synthetic already measured."""

    def test_tilt_error_reproduces_the_measured_synthetic_runs(self):
        self.assertAlmostEqual(vf.height_error_mm(3.06, 10.0), 0.0456, delta=0.001)
        self.assertAlmostEqual(vf.height_error_mm(3.06, 20.0), 0.1847, delta=0.001)

    def test_zero_tilt_costs_nothing(self):
        self.assertAlmostEqual(vf.height_error_mm(3.06, 0.0), 0.0, places=12)

    def test_error_grows_with_tilt(self):
        vals = [vf.height_error_mm(3.06, a) for a in (1, 2, 3, 5, 10, 20)]
        self.assertEqual(vals, sorted(vals))

    def test_gap_and_tilt_conversions_are_inverses(self):
        for span in (20.0, 50.0, 95.0):
            gap = vf.max_gap_for(bound(), span)
            self.assertAlmostEqual(vf.tilt_from_gap(gap, span), bound(), places=6)


# ---------------------------------------------------------------------------
# evidence states
# ---------------------------------------------------------------------------

class TestEvidenceStates(unittest.TestCase):
    def test_a_surveyed_panel_can_pass(self):
        issues, summary, panels = vf.validate(register())
        self.assertEqual(codes(issues), [])
        self.assertTrue(summary["verified"])
        self.assertEqual(panels["P01"]["derived_status"], vf.PASS)

    def test_a_blank_template_is_unverified_not_flat(self):
        reg = vf.template()
        self.assertEqual(statuses(reg), {"P01": vf.UNVERIFIED})
        self.assertFalse(verdict(reg))

    def test_every_missing_field_yields_unverified(self):
        for field in ("instrument", "instrument_resolution_mm", "operator",
                      "measured_at", "backing_id", "mounting_method",
                      "max_gap_long_mm", "max_gap_short_mm",
                      "straightedge_span_short_mm", "frame_flush_check"):
            reg = register({"P01": passing_panel(**{field: None}, status=None)})
            issues, _s, panels = vf.validate(reg)
            self.assertEqual(panels["P01"]["derived_status"], vf.UNVERIFIED, field)
            self.assertIn("FLATNESS_EVIDENCE_MISSING", codes(issues), field)

    def test_unverified_backing_is_not_accepted(self):
        for bad in (None, False, "yes", 1):
            reg = register({"P01": passing_panel(backing_rigid_flat_verified=bad,
                                                 status=None)})
            self.assertEqual(statuses(reg)["P01"], vf.UNVERIFIED, bad)

    def test_an_empty_register_verifies_nothing(self):
        issues, summary, _p = vf.validate(register(panels={}))
        self.assertIn("NO_PANELS_RECORDED", codes(issues))
        self.assertFalse(summary["verified"])

    def test_a_non_object_panel_record_is_unverified(self):
        reg = register({"P01": "flat enough"})
        issues, _s, panels = vf.validate(reg)
        self.assertEqual(panels["P01"]["derived_status"], vf.UNVERIFIED)
        self.assertIn("BAD_PANEL_RECORD", codes(issues))

    def test_validation_is_deterministic(self):
        reg = register()
        self.assertEqual(vf.validate(reg), vf.validate(reg))


class TestFailStates(unittest.TestCase):
    def test_tilt_beyond_the_model_bound_fails(self):
        """A gap implying more than the budgeted tilt is a FAIL, not a warning."""
        over = vf.max_gap_for(bound(), 50.0) * 1.5
        reg = register({"P01": passing_panel(max_gap_long_mm=over, status=None)})
        issues, _s, panels = vf.validate(reg)
        self.assertEqual(panels["P01"]["derived_status"], vf.FAIL)
        self.assertIn("LOCAL_TILT_BEYOND_MODEL_BOUND", codes(issues))

    def test_the_short_axis_can_be_the_binding_one(self):
        """0.26 mm over 20 mm is the same tilt as 0.66 mm over 50 mm."""
        gap = vf.max_gap_for(bound(), 50.0)          # fine on the long axis
        reg = register({"P01": passing_panel(max_gap_short_mm=gap, status=None)})
        issues, _s, panels = vf.validate(reg)
        self.assertEqual(panels["P01"]["derived_status"], vf.FAIL)
        self.assertIn("LOCAL_TILT_BEYOND_MODEL_BOUND", codes(issues))

    def test_a_gap_exactly_at_the_limit_passes(self):
        reg = register({"P01": passing_panel(
            max_gap_long_mm=vf.max_gap_for(bound(), 50.0),
            max_gap_short_mm=vf.max_gap_for(bound(), 20.0))})
        self.assertEqual(statuses(reg)["P01"], vf.PASS)

    def test_frame_not_flush_fails(self):
        for state in ("ROCK", "GAP"):
            reg = register({"P01": passing_panel(frame_flush_check=state,
                                                status=None)})
            issues, _s, panels = vf.validate(reg)
            self.assertEqual(panels["P01"]["derived_status"], vf.FAIL, state)
            self.assertIn("FRAME_NOT_FLUSH", codes(issues), state)

    def test_flush_check_skipped_is_unverified(self):
        reg = register({"P01": passing_panel(frame_flush_check="NOT_CHECKED",
                                            status=None)})
        issues, _s, panels = vf.validate(reg)
        self.assertEqual(panels["P01"]["derived_status"], vf.UNVERIFIED)
        self.assertIn("FRAME_FLUSH_NOT_CHECKED", codes(issues))

    def test_an_instrument_too_coarse_for_the_limit_is_rejected(self):
        reg = register({"P01": passing_panel(instrument_resolution_mm=1.0,
                                            status=None)})
        issues, _s, panels = vf.validate(reg)
        self.assertIn("INSTRUMENT_CANNOT_RESOLVE_LIMIT", codes(issues))
        self.assertEqual(panels["P01"]["derived_status"], vf.UNVERIFIED)

    def test_weak_mounting_warns_but_does_not_block(self):
        for method in vf.MOUNTING_ADVISORY:
            reg = register({"P01": passing_panel(mounting_method=method)})
            issues, summary, _p = vf.validate(reg)
            self.assertIn("WEAK_MOUNTING", codes(issues, "WARN"), method)
            self.assertTrue(summary["verified"], method)


class TestNoSelfCertification(unittest.TestCase):
    def test_a_declared_pass_cannot_override_its_own_measurements(self):
        over = vf.max_gap_for(bound(), 50.0) * 2.0
        reg = register({"P01": passing_panel(max_gap_long_mm=over, status="PASS")})
        issues, _s, panels = vf.validate(reg)
        self.assertIn("STATUS_CONTRADICTS_EVIDENCE", codes(issues))
        self.assertEqual(panels["P01"]["derived_status"], vf.FAIL)

    def test_a_declared_pass_cannot_stand_in_for_missing_evidence(self):
        reg = register({"P01": {"status": "PASS"}})
        issues, _s, panels = vf.validate(reg)
        self.assertEqual(panels["P01"]["derived_status"], vf.UNVERIFIED)
        self.assertIn("STATUS_CONTRADICTS_EVIDENCE", codes(issues))

    def test_an_unknown_status_string_is_rejected(self):
        reg = register({"P01": passing_panel(status="FLAT")})
        issues, _s, _p = vf.validate(reg)
        self.assertIn("BAD_STATUS", codes(issues))

    def test_omitting_status_is_allowed_because_evidence_decides(self):
        reg = register({"P01": passing_panel(status=None)})
        issues, summary, panels = vf.validate(reg)
        self.assertEqual(panels["P01"]["derived_status"], vf.PASS)
        self.assertEqual(codes(issues), [])
        self.assertTrue(summary["verified"])

    def test_a_non_passing_panel_wants_a_disposition_note(self):
        reg = register({"P01": passing_panel(frame_flush_check="ROCK",
                                            status="FAIL", notes="")})
        issues, _s, _p = vf.validate(reg)
        self.assertIn("NO_DISPOSITION_NOTE", codes(issues, "WARN"))


class TestManifestCrossCheck(unittest.TestCase):
    def _man(self, **over):
        run = {"run_id": "P01-A-OP1-R1", "panel_id": "P01", "declared_flat": True}
        run.update(over)
        return {"runs": [run]}

    def test_a_run_on_a_passing_panel_is_clean(self):
        issues, summary, _p = vf.validate(register(), self._man())
        self.assertEqual(codes(issues), [])
        self.assertTrue(summary["verified"])

    def test_a_run_on_an_unregistered_panel_is_rejected(self):
        issues, _s, _p = vf.validate(register(), self._man(panel_id="P07"))
        self.assertIn("NO_FLATNESS_RECORD_FOR_PANEL", codes(issues))

    def test_a_run_on_an_unverified_panel_is_rejected(self):
        reg = register({"P01": passing_panel(max_gap_long_mm=None, status=None)})
        issues, _s, _p = vf.validate(reg, self._man())
        self.assertIn("RUN_ON_UNVERIFIED_PANEL", codes(issues))

    def test_declared_flat_without_evidence_is_named_explicitly(self):
        reg = register({"P01": passing_panel(frame_flush_check="ROCK",
                                            status=None, notes="shimmed")})
        issues, _s, _p = vf.validate(reg, self._man(declared_flat=True))
        self.assertIn("DECLARED_FLAT_WITHOUT_EVIDENCE", codes(issues))

    def test_absent_declared_flat_is_rejected(self):
        man = {"runs": [{"run_id": "R1", "panel_id": "P01"}]}
        issues, _s, _p = vf.validate(register(), man)
        self.assertIn("DECLARED_FLAT_ABSENT", codes(issues))

    def test_runs_without_a_panel_id_are_skipped_not_assumed(self):
        man = {"runs": [{"run_id": "R1", "declared_flat": True}]}
        issues, _s, _p = vf.validate(register(), man)
        self.assertNotIn("NO_FLATNESS_RECORD_FOR_PANEL", codes(issues))


class TestRunnerRefusesUnstatedFlatness(unittest.TestCase):
    def test_scaffold_no_longer_defaults_to_flat(self):
        import run_real_batch as rrb
        tmp = tempfile.mkdtemp()
        try:
            caps = os.path.join(tmp, "caps", "P01", "A", "OP1", "R1")
            os.makedirs(caps)
            open(os.path.join(caps, "f1.png"), "wb").close()
            out = os.path.join(tmp, "m.json")
            buf, old = io.StringIO(), sys.stdout
            sys.stdout = buf
            try:
                rrb.scaffold(os.path.join(tmp, "caps"), out)
            finally:
                sys.stdout = old
            r = load_json(out)["runs"][0]
            self.assertIsNone(r["declared_flat"])
            self.assertIn("flatness_record", r)
        finally:
            shutil.rmtree(tmp)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _cli(self, argv):
        buf = io.StringIO()
        old_o, old_e = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf, buf
        try:
            rc = vf.main(argv)
        finally:
            sys.stdout, sys.stderr = old_o, old_e
        return rc, buf.getvalue()

    def test_template_then_verify_is_no(self):
        p = os.path.join(self.tmp, "reg.json")
        self.assertEqual(self._cli(["--template", p])[0], 0)
        rc, txt = self._cli(["--register", p])
        self.assertEqual(rc, 1)
        self.assertIn("B4_FLATNESS_VERIFIED = NO", txt)

    def test_a_surveyed_register_exits_zero(self):
        p = os.path.join(self.tmp, "ok.json")
        dump_json(p, register())
        rc, txt = self._cli(["--register", p])
        self.assertEqual(rc, 0)
        self.assertIn("B4_FLATNESS_VERIFIED = YES", txt)

    def test_missing_file_exits_two(self):
        rc, txt = self._cli(["--register", os.path.join(self.tmp, "nope.json")])
        self.assertEqual(rc, 2)
        self.assertIn("B4_FLATNESS_VERIFIED = NO", txt)

    def test_json_out_records_the_verdict(self):
        p = os.path.join(self.tmp, "ok.json")
        out = os.path.join(self.tmp, "res.json")
        dump_json(p, register())
        self._cli(["--register", p, "--json-out", out])
        got = load_json(out)
        self.assertEqual(got["B4_FLATNESS_VERIFIED"], "YES")
        self.assertEqual(got["panels"]["P01"]["derived_status"], vf.PASS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
