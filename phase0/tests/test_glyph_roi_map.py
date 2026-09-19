"""Tests for the pre-registered glyph / ROI map (blocker B3).

These test **location machinery only**.  No test asserts a measured height, none
uses physical data, and none selects which glyphs the experiment will use — that is
B5.  The map is derived from committed code, so several tests are consistency
checks between the coupon generator and `p0.render`.
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

import make_coupons_svg as mc                     # noqa: E402
import make_glyph_map as mgm                      # noqa: E402
import validate_roi_map as vrm                    # noqa: E402

from p0.core import dump_json, load_json          # noqa: E402
from p0.render import glyph_bbox_mm               # noqa: E402

COMMITTED_MAP = os.path.join(ROOT, "fixtures", "physical", "coupons",
                             "glyph_map.json")
FRAME_CERT = os.path.join(ROOT, "config", "frames", "FRAME-SYN-0001.json")
GATE_POLICY = os.path.join(ROOT, "config", "gate_policy_v1.json")


def the_map():
    return load_json(COMMITTED_MAP)


def glyph(key="P01:BAR_I:3.00:1"):
    for g in the_map()["glyphs"]:
        if g["glyph_key"] == key:
            return g
    raise KeyError(key)


def registration_for(g, theta_deg=0.0, u_mm=0.02, span=None, **over):
    """A mounting that places glyph `g` exactly at the fiducial origin."""
    t = math.radians(theta_deg)
    px, py = g["panel_x_mm"], g["panel_y_mm"]
    c, s = math.cos(t), math.sin(t)
    # solve panel_to_fiducial(px, py, ox, oy, t) == (0, 0)
    ox = -(px * c + py * s)
    oy = -(px * s - py * c)
    w = mc.COUPON[0] if span is None else span
    reg = {"corner_top_left_mm": [ox, oy],
           "corner_top_right_mm": [ox + w * c, oy + w * s],
           "u_mm": u_mm, "top_left_identified_by": "PANEL_LABEL_TEXT",
           "method": "CALIPER_TWO_POINT", "operator": "OP1",
           "measured_at": "2026-01-01T00:00:00Z"}
    reg.update(over)
    return reg


def run_for(g, reg=None, roi=None, **over):
    panel, shape, h, idx = g["glyph_key"].split(":")
    r = {"run_id": "R-" + g["glyph_key"], "panel_id": panel, "glyph_label": shape,
         "nominal_h_mm": g["nominal_h_mm"], "shape_class": g["shape_class"],
         "glyph_index": int(idx), "device": "A", "operator": "OP1", "repeat": "R1",
         "frames": ["f.png"], "registration": reg or registration_for(g)}
    if roi is not None:
        r["roi_mm"] = roi
    r.update(over)
    return r


def manifest_for(runs):
    return {"runs": runs if isinstance(runs, list) else [runs]}


def check(manifest, with_gate=False):
    cert = load_json(FRAME_CERT)
    margin = load_json(GATE_POLICY)["min_hull_margin_mm"] if with_gate else None
    return vrm.validate(manifest, the_map(), cert, margin)


def codes(issues, severity="ERROR"):
    return sorted(i["code"] for i in issues if i["severity"] == severity)


def filled_roi(g, reg=None):
    reg = reg or registration_for(g)
    return [round(v, 6) for v in vrm.compute_roi(g, reg, mc.COUPON[0])["roi_mm"]]


# ---------------------------------------------------------------------------
# the map itself
# ---------------------------------------------------------------------------

class TestGlyphMapDerivation(unittest.TestCase):
    def test_committed_map_matches_a_fresh_derivation(self):
        """Determinism: the map is derived, never hand-edited."""
        fresh = mgm.build(mgm.load_panels())
        self.assertEqual(the_map(), fresh)

    def test_derivation_is_stable_across_calls(self):
        a = mgm.build(mgm.load_panels())
        b = mgm.build(mgm.load_panels())
        self.assertEqual(a, b)
        self.assertEqual(a["map_hash"], b["map_hash"])

    def test_map_covers_every_glyph_instance(self):
        m = the_map()
        self.assertEqual(m["n_glyphs"], 400)
        self.assertEqual(len(m["glyphs"]), 400)
        self.assertEqual(len({g["glyph_key"] for g in m["glyphs"]}), 400)

    def test_every_panel_has_all_heights_and_shapes(self):
        m = the_map()
        by_panel = {}
        for g in m["glyphs"]:
            by_panel.setdefault(g["panel_id"], []).append(g)
        self.assertEqual(len(by_panel), 20)
        for pid, gs in by_panel.items():
            self.assertEqual(len(gs), 20, pid)
            self.assertEqual({g["nominal_h_mm"] for g in gs}, set(mc.HEIGHTS), pid)
            self.assertEqual({g["glyph_shape"] for g in gs}, set(mc.SHAPES), pid)

    def test_roi_size_equals_the_repository_bbox_function(self):
        for g in the_map()["glyphs"]:
            w, h = glyph_bbox_mm(g["glyph_shape"], g["nominal_h_mm"], 0.0)
            self.assertAlmostEqual(g["roi_w_mm"], w, places=6, msg=g["glyph_key"])
            self.assertAlmostEqual(g["roi_h_mm"], h, places=6, msg=g["glyph_key"])

    def test_layout_matches_the_coupon_generator_stepping(self):
        """Independent replay of `coupon()`'s own row/column arithmetic."""
        for panel in mgm.load_panels():
            heights = [float(h) for h in panel["nominal_heights_mm"]]
            yy = 14.0
            for h in heights:
                xx = 8.0
                for shape in mc.SHAPES:
                    g = glyph(mgm.glyph_key(panel["panel_id"], shape, h, 1))
                    self.assertAlmostEqual(g["panel_x_mm"], xx, places=6)
                    self.assertAlmostEqual(g["panel_y_mm"], yy, places=6)
                    xx += max(1.2 * h, 4.0) + 2.0
                yy += max(h * 1.9, 7.0)

    def test_staggered_panels_really_differ(self):
        """panels.json reverses the height order on alternate panels."""
        a = glyph("P01:BAR_I:6.00:1")["panel_y_mm"]
        b = glyph("P02:BAR_I:6.00:1")["panel_y_mm"]
        self.assertNotAlmostEqual(a, b)

    def test_every_glyph_fits_inside_the_coupon(self):
        cw, ch = mc.COUPON
        for g in the_map()["glyphs"]:
            self.assertLess(g["panel_x_mm"] + g["roi_w_mm"] / 2, cw, g["glyph_key"])
            self.assertLess(g["panel_y_mm"] + g["roi_h_mm"] / 2, ch, g["glyph_key"])

    def test_scan_span_never_reaches_the_neighbouring_row(self):
        """0.725 * roi_h is p0/measure.py's `span_n`; rows must clear it."""
        by_panel_col = {}
        for g in the_map()["glyphs"]:
            by_panel_col.setdefault((g["panel_id"], g["glyph_shape"]), []).append(g)
        for (_pid, _shape), gs in by_panel_col.items():
            gs = sorted(gs, key=lambda g: g["panel_y_mm"])
            for lo, hi in zip(gs, gs[1:]):
                gap = hi["panel_y_mm"] - lo["panel_y_mm"]
                self.assertLess(0.725 * lo["roi_h_mm"], gap)
                self.assertLess(0.725 * hi["roi_h_mm"], gap)

    def test_tolerance_is_the_binding_of_the_two_derived_limits(self):
        for g in the_map()["glyphs"]:
            self.assertAlmostEqual(
                g["roi_tolerance_mm"],
                min(0.5 * g["roi_w_mm"], 0.225 * g["roi_h_mm"]), places=6)

    def test_smallest_tolerance_is_the_thin_small_glyph(self):
        m = the_map()
        worst = min(m["glyphs"], key=lambda g: g["roi_tolerance_mm"])
        self.assertEqual(worst["glyph_shape"], "BAR_I")
        self.assertAlmostEqual(worst["nominal_h_mm"], 1.2)
        self.assertAlmostEqual(worst["roi_tolerance_mm"], 0.108, places=6)

    def test_map_records_the_nominal_prohibition(self):
        self.assertIn("never", the_map()["prohibition"])

    def test_cli_check_passes_on_the_committed_map(self):
        buf, old = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            rc = mgm.main(["--check", COMMITTED_MAP])
        finally:
            sys.stdout = old
        self.assertEqual(rc, 0)

    def test_cli_check_fails_on_a_tampered_map(self):
        tmp = tempfile.mkdtemp()
        try:
            m = the_map()
            m["glyphs"][0]["panel_x_mm"] += 0.5
            p = os.path.join(tmp, "tampered.json")
            dump_json(p, m)
            buf, old = io.StringIO(), sys.stdout
            sys.stdout = buf
            try:
                rc = mgm.main(["--check", p])
            finally:
                sys.stdout = old
            self.assertEqual(rc, 1)
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# panel -> fiducial transform
# ---------------------------------------------------------------------------

class TestTransform(unittest.TestCase):
    def test_identity_placement_puts_the_glyph_at_the_origin(self):
        g = glyph()
        self.assertEqual(filled_roi(g)[:2], [0.0, 0.0])

    def test_panel_y_is_down_and_fiducial_y_is_up(self):
        ox, oy = 0.0, 0.0
        x, y = vrm.panel_to_fiducial(10.0, 20.0, ox, oy, 0.0)
        self.assertAlmostEqual(x, 10.0)
        self.assertAlmostEqual(y, -20.0)

    def test_transform_is_a_rigid_motion(self):
        """Distances between glyphs survive the transform."""
        a, b = glyph("P01:BAR_I:3.00:1"), glyph("P01:RING_O:3.00:1")
        for theta in (0.0, 3.0, -7.5, 45.0):
            t = math.radians(theta)
            pa = vrm.panel_to_fiducial(a["panel_x_mm"], a["panel_y_mm"], 1.0, 2.0, t)
            pb = vrm.panel_to_fiducial(b["panel_x_mm"], b["panel_y_mm"], 1.0, 2.0, t)
            self.assertAlmostEqual(
                math.hypot(pa[0] - pb[0], pa[1] - pb[1]),
                math.hypot(a["panel_x_mm"] - b["panel_x_mm"],
                           a["panel_y_mm"] - b["panel_y_mm"]), places=9)

    def test_rotation_is_derived_from_the_two_corners(self):
        g = glyph()
        for theta in (0.0, 2.0, -4.0):
            c = vrm.compute_roi(g, registration_for(g, theta_deg=theta),
                                mc.COUPON[0])
            self.assertAlmostEqual(c["theta_deg"], theta, places=6)

    def test_uncertainty_grows_with_the_lever_arm(self):
        near = glyph("P01:BAR_I:1.20:1")
        far = glyph("P01:RING_O:6.00:1")
        cn = vrm.compute_roi(near, registration_for(near), mc.COUPON[0])
        cf = vrm.compute_roi(far, registration_for(far), mc.COUPON[0])
        self.assertLess(cn["u_reg_mm"], cf["u_reg_mm"])

    def test_registration_needs_two_distinct_points(self):
        g = glyph()
        reg = registration_for(g)
        reg["corner_top_right_mm"] = list(reg["corner_top_left_mm"])
        with self.assertRaises(vrm.RoiMapError):
            vrm.compute_roi(g, reg, mc.COUPON[0])

    def test_registration_rejects_non_numeric_corners(self):
        g = glyph()
        for bad in (None, "0,0", [0.0], [0.0, "x"], [True, 1.0]):
            reg = registration_for(g)
            reg["corner_top_left_mm"] = bad
            with self.assertRaises(vrm.RoiMapError):
                vrm.compute_roi(g, reg, mc.COUPON[0])

    def test_registration_rejects_missing_uncertainty(self):
        g = glyph()
        for bad in (None, -1.0, "0.02", True):
            reg = registration_for(g)
            reg["u_mm"] = bad
            with self.assertRaises(vrm.RoiMapError):
                vrm.compute_roi(g, reg, mc.COUPON[0])


# ---------------------------------------------------------------------------
# manifest validation
# ---------------------------------------------------------------------------

class TestManifestValidation(unittest.TestCase):
    def test_a_computed_roi_is_accepted(self):
        g = glyph()
        issues, summary, _c = check(manifest_for(run_for(g, roi=filled_roi(g))))
        self.assertEqual(codes(issues), [])
        self.assertEqual(codes(issues, "WARN"), [])
        self.assertEqual(summary["runs_with_computed_roi"], 1)

    def test_missing_roi_is_rejected(self):
        issues, _s, _c = check(manifest_for(run_for(glyph())))
        self.assertIn("MISSING_ROI", codes(issues))

    def test_scaffold_placeholder_roi_is_rejected_by_name(self):
        g = glyph()
        issues, _s, _c = check(manifest_for(
            run_for(g, roi=list(vrm.SCAFFOLD_PLACEHOLDER_ROI))))
        self.assertIn("SCAFFOLD_PLACEHOLDER_ROI", codes(issues))

    def test_todo_glyph_label_is_rejected(self):
        g = glyph()
        issues, _s, _c = check(manifest_for(
            run_for(g, roi=filled_roi(g), glyph_label="TODO")))
        self.assertIn("GLYPH_NOT_PREREGISTERED", codes(issues))

    def test_unmapped_glyph_is_rejected(self):
        g = glyph()
        for over in ({"panel_id": "P99"}, {"glyph_label": "Q"},
                     {"nominal_h_mm": 5.0}, {"glyph_index": 7}):
            r = run_for(g, roi=filled_roi(g), **over)
            issues, _s, _c = check(manifest_for(r))
            self.assertIn("GLYPH_NOT_IN_MAP", codes(issues), over)

    def test_wrong_panel_glyph_association_is_rejected(self):
        """Right glyph name, wrong panel's registration -> wrong region."""
        g1, g2 = glyph("P01:BAR_I:3.00:1"), glyph("P01:RING_O:6.00:1")
        r = run_for(g1, reg=registration_for(g2), roi=filled_roi(g1))
        issues, _s, _c = check(manifest_for(r))
        self.assertIn("ROI_WRONG_GLYPH", codes(issues))

    def test_shape_class_mismatch_is_rejected(self):
        g = glyph("P01:RING_O:3.00:1")
        r = run_for(g, roi=filled_roi(g), shape_class="FLAT_TOP")
        issues, _s, _c = check(manifest_for(r))
        self.assertIn("SHAPE_CLASS_MISMATCH", codes(issues))

    def test_glyph_key_contradiction_is_rejected(self):
        g = glyph()
        r = run_for(g, roi=filled_roi(g), glyph_key="P02:H:2.00:1")
        issues, _s, _c = check(manifest_for(r))
        self.assertIn("GLYPH_KEY_MISMATCH", codes(issues))

    def test_missing_nominal_height_is_rejected(self):
        g = glyph()
        for bad in (None, "3.0", True):
            r = run_for(g, roi=filled_roi(g), nominal_h_mm=bad)
            issues, _s, _c = check(manifest_for(r))
            self.assertIn("MISSING_NOMINAL_HEIGHT", codes(issues), bad)

    def test_unit_and_shape_errors_in_roi_are_rejected(self):
        g = glyph()
        good = filled_roi(g)
        for bad, code in (
                ([0.0, 0.0, 540.0, 3000.0], "ROI_SIZE_NOT_FROM_MAP"),   # microns
                ([0.0, 0.0], "BAD_ROI_SHAPE"),
                ("0,0,0.54,3.0", "BAD_ROI_SHAPE"),
                ([0.0, 0.0, 0.54, 3.0, 1.0], "BAD_ROI_SHAPE"),
                ([0.0, 0.0, -0.54, 3.0], "NONPOSITIVE_ROI_SIZE"),
                ([0.0, 0.0, 0.0, 3.0], "NONPOSITIVE_ROI_SIZE"),
                ([good[0], good[1], good[3], good[2]], "ROI_SIZE_NOT_FROM_MAP"),
        ):
            issues, _s, _c = check(manifest_for(run_for(g, roi=bad)))
            self.assertIn(code, codes(issues), bad)

    def test_swapped_width_and_height_is_named_as_such(self):
        g = glyph()
        good = filled_roi(g)
        issues, _s, _c = check(manifest_for(
            run_for(g, roi=[good[0], good[1], good[3], good[2]])))
        detail = " ".join(i["detail"] for i in issues)
        self.assertIn("swapped", detail)

    def test_a_hand_nudged_roi_is_rejected_even_within_tolerance(self):
        """Anti-tuning: the ROI must be the computed value, not an adjusted one."""
        g = glyph()
        good = filled_roi(g)
        nudged = [good[0] + 0.05, good[1], good[2], good[3]]
        self.assertLess(0.05, g["roi_tolerance_mm"])          # inside the budget
        issues, _s, _c = check(manifest_for(run_for(g, roi=nudged)))
        self.assertIn("ROI_ADJUSTED_BY_HAND", codes(issues))

    def test_a_substituted_neighbour_glyph_is_rejected(self):
        """Operator cannot silently point at the glyph next door."""
        g = glyph("P01:BAR_I:3.00:1")
        nb = glyph("P01:H:3.00:1")
        roi = filled_roi(g)
        offset = [roi[0] + (nb["panel_x_mm"] - g["panel_x_mm"]), roi[1],
                  roi[2], roi[3]]
        issues, _s, _c = check(manifest_for(run_for(g, roi=offset)))
        self.assertIn("ROI_WRONG_GLYPH", codes(issues))

    def test_missing_registration_is_rejected(self):
        g = glyph()
        r = run_for(g, roi=filled_roi(g))
        del r["registration"]
        issues, _s, _c = check(manifest_for(r))
        self.assertIn("MISSING_REGISTRATION", codes(issues))

    def test_panel_level_registration_is_used_when_the_run_has_none(self):
        g = glyph()
        r = run_for(g, roi=filled_roi(g))
        reg = r.pop("registration")
        man = {"runs": [r], "registrations": {g["panel_id"]: reg}}
        issues, summary, _c = check(man)
        self.assertEqual(codes(issues), [])
        self.assertEqual(summary["panels_registered"], [g["panel_id"]])

    def test_unidentified_origin_corner_is_rejected(self):
        g = glyph()
        reg = registration_for(g)
        reg["top_left_identified_by"] = "TBD"
        issues, _s, _c = check(manifest_for(run_for(g, reg=reg,
                                                   roi=filled_roi(g))))
        self.assertIn("REGISTRATION_ORIGIN_UNIDENTIFIED", codes(issues))

    def test_implausible_corner_span_is_rejected(self):
        """Catches wrong corners, a rotated mounting, or a mis-scaled print."""
        g = glyph()
        reg = registration_for(g, span=mc.COUPON[1])          # used the short edge
        issues, _s, _c = check(manifest_for(run_for(g, reg=reg)))
        self.assertIn("REGISTRATION_SPAN_IMPLAUSIBLE", codes(issues))

    def test_registration_uncertainty_beyond_the_roi_budget_is_rejected(self):
        g = glyph("P01:BAR_I:1.20:1")
        reg = registration_for(g, u_mm=0.5)
        issues, _s, _c = check(manifest_for(run_for(g, reg=reg)))
        self.assertIn("REGISTRATION_UNCERTAINTY_EXCEEDS_ROI_TOLERANCE",
                      codes(issues))

    def test_a_careful_caliper_survey_meets_the_smallest_budget(self):
        """The documented 0.02 mm survey uncertainty is good enough everywhere."""
        for g in the_map()["glyphs"]:
            c = vrm.compute_roi(g, registration_for(g, u_mm=0.02), mc.COUPON[0])
            self.assertLess(c["u_reg_mm"], g["roi_tolerance_mm"], g["glyph_key"])

    def test_large_mounting_rotation_warns_but_does_not_block(self):
        g = glyph()
        reg = registration_for(g, theta_deg=12.0)
        issues, _s, _c = check(manifest_for(run_for(g, reg=reg,
                                                   roi=filled_roi(g, reg))))
        self.assertIn("LARGE_MOUNTING_ROTATION", codes(issues, "WARN"))
        self.assertEqual(codes(issues), [])

    def test_duplicate_run_id_is_rejected(self):
        g = glyph()
        r = run_for(g, roi=filled_roi(g))
        issues, _s, _c = check(manifest_for([r, dict(r)]))
        self.assertIn("DUPLICATE_RUN_ID", codes(issues))

    def test_duplicate_glyph_cell_is_rejected(self):
        g = glyph()
        a = run_for(g, roi=filled_roi(g))
        b = dict(a, run_id="R-other")
        issues, _s, _c = check(manifest_for([a, b]))
        self.assertIn("DUPLICATE_GLYPH_CELL", codes(issues))

    def test_repeats_that_differ_are_allowed(self):
        g = glyph()
        a = run_for(g, roi=filled_roi(g))
        b = dict(a, run_id="R-r2", repeat="R2")
        issues, _s, _c = check(manifest_for([a, b]))
        self.assertEqual(codes(issues), [])

    def test_a_duplicate_map_key_is_refused_outright(self):
        m = the_map()
        m["glyphs"].append(dict(m["glyphs"][0]))
        with self.assertRaises(vrm.RoiMapError):
            vrm.validate({"runs": []}, m, {}, None)

    def test_glyph_outside_the_frame_window_is_rejected(self):
        """Visibility is checked before capture, not discovered afterwards."""
        g = glyph()
        reg = registration_for(g)
        reg["corner_top_left_mm"] = [reg["corner_top_left_mm"][0] + 40.0,
                                     reg["corner_top_left_mm"][1]]
        reg["corner_top_right_mm"] = [reg["corner_top_right_mm"][0] + 40.0,
                                      reg["corner_top_right_mm"][1]]
        issues, _s, _c = check(manifest_for(run_for(g, reg=reg,
                                                   roi=filled_roi(g, reg))))
        self.assertIn("GLYPH_OUTSIDE_FRAME_WINDOW", codes(issues))

    def test_validation_is_deterministic(self):
        g = glyph()
        man = manifest_for(run_for(g, roi=filled_roi(g)))
        self.assertEqual(check(man), check(man))

    def test_missing_run_id_is_rejected(self):
        g = glyph()
        r = run_for(g, roi=filled_roi(g))
        r["run_id"] = None
        issues, _s, _c = check(manifest_for(r))
        self.assertIn("MISSING_RUN_ID", codes(issues))


class TestMisplacedRoiAbstains(unittest.TestCase):
    """A wrong ROI must abstain, not return a confident wrong height.

    This is the safety property behind the failure handling in
    `docs/B3_GLYPH_ROI_MAP.md` §5.  It measures the *existing* pipeline on
    synthetic renders; no measurement code is involved in B3 itself.
    """

    @classmethod
    def setUpClass(cls):
        from p0.camera import Camera
        from p0.core import obj_hash
        from p0.render import SceneSpec, render_burst
        cls.cert = load_json(FRAME_CERT)
        cls.prof = load_json(os.path.join(ROOT, "config", "cameras",
                                          "CAM-SYN-A.json"))
        cls.cam = Camera.from_dict(cls.prof["camera"])
        cls.mp = load_json(os.path.join(ROOT, "config",
                                        "measurand_policy_v1.json"))
        cls.gp = load_json(GATE_POLICY)
        cls.um = load_json(os.path.join(ROOT, "config",
                                        "uncertainty_model_v1.json"))
        spec = SceneSpec(glyph_shape="BAR_I", design_h_mm=1.2, blur_sigma_px=0.6,
                         noise_sigma=0.002, ink_spread_mm=0.02, ss_marker=6,
                         ss_glyph=8)
        cls.frames, gts = render_burst(cls.cam, cls.cert, spec,
                                       "B3-" + obj_hash(spec.to_dict())[:8], n=2)
        cls.gt = gts[0]

    def _measure(self, dx, dy):
        from p0.pipeline import measure_run
        cx, cy = self.gt["glyph_center_mm"]
        w, h = self.gt["glyph_bbox_mm"]
        return measure_run(self.frames, self.cam, self.cert, self.mp, self.gp,
                           self.um, (cx + dx, cy + dy, w, h),
                           self.gt["shape_class"],
                           0.9 * self.gt["true_ink_height_mm"], "B3",
                           context={"profile_id": self.prof["profile_id"],
                                    "z_calib_mm": self.prof["z_calib_mm"]})

    def test_on_target_roi_measures(self):
        res = self._measure(0.0, 0.0)
        self.assertEqual(res["status"], "MEASURED")
        self.assertAlmostEqual(res["measurement"]["h_mm"],
                               self.gt["true_ink_height_mm"], delta=0.02)

    def test_offset_beyond_the_budget_abstains(self):
        g = glyph("P01:BAR_I:1.20:1")
        for dx, dy in ((4 * g["roi_tolerance_mm"], 0.0),
                       (0.0, 4 * g["roi_tolerance_mm"])):
            res = self._measure(dx, dy)
            self.assertNotEqual(res["status"], "MEASURED", (dx, dy))
            self.assertIsNone(res["measurement"]["h_mm"], (dx, dy))

    def test_a_grossly_wrong_roi_abstains_rather_than_measuring_paper(self):
        res = self._measure(3.0, 3.0)
        self.assertNotEqual(res["status"], "MEASURED")
        self.assertIsNone(res["measurement"]["h_mm"])


class TestFillAndCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_fill_writes_the_computed_roi_and_its_provenance(self):
        g = glyph()
        man = manifest_for(run_for(g))
        _i, _s, computed = check(man)
        out = vrm.fill(man, the_map(), computed)
        r = out["runs"][0]
        self.assertEqual(r["roi_mm"], filled_roi(g))
        self.assertEqual(r["roi_source"], "COMPUTED_FROM_GLYPH_MAP")
        self.assertEqual(r["glyph_map_hash"], the_map()["map_hash"])

    def test_fill_then_validate_is_clean(self):
        g = glyph()
        man = manifest_for(run_for(g))
        _i, _s, computed = check(man)
        issues, _s2, _c = check(vrm.fill(man, the_map(), computed))
        self.assertEqual(codes(issues), [])

    def test_fill_does_not_mutate_the_input(self):
        g = glyph()
        man = manifest_for(run_for(g))
        _i, _s, computed = check(man)
        vrm.fill(man, the_map(), computed)
        self.assertNotIn("roi_mm", man["runs"][0])

    def _cli(self, argv, stream="out"):
        buf = io.StringIO()
        old_o, old_e = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = (buf, buf)
        try:
            rc = vrm.main(argv)
        finally:
            sys.stdout, sys.stderr = old_o, old_e
        return rc, buf.getvalue()

    def test_cli_rejects_then_accepts_after_fill(self):
        g = glyph()
        p = os.path.join(self.tmp, "m.json")
        q = os.path.join(self.tmp, "filled.json")
        dump_json(p, manifest_for(run_for(g)))
        rc, txt = self._cli(["--manifest", p])
        self.assertEqual(rc, 1)
        self.assertIn("REJECTED", txt)
        self._cli(["--manifest", p, "--fill", q])
        rc, txt = self._cli(["--manifest", q])
        self.assertEqual(rc, 0)
        self.assertIn("ACCEPTED", txt)

    def test_cli_exits_two_on_an_unreadable_manifest(self):
        rc, txt = self._cli(["--manifest", os.path.join(self.tmp, "nope.json")])
        self.assertEqual(rc, 2)
        self.assertIn("REJECTED", txt)

    def test_scaffold_no_longer_emits_a_plausible_stub_roi(self):
        """The old stub was a valid-looking box at the frame centre."""
        import run_real_batch as rrb
        caps = os.path.join(self.tmp, "caps", "P01", "A", "OP1", "R1")
        os.makedirs(caps)
        open(os.path.join(caps, "f1.png"), "wb").close()
        out = os.path.join(self.tmp, "scaffold.json")
        buf, old = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            rrb.scaffold(os.path.join(self.tmp, "caps"), out)
        finally:
            sys.stdout = old
        r = load_json(out)["runs"][0]
        self.assertIsNone(r["roi_mm"])
        self.assertEqual(r["roi_source"], "UNSET")
        self.assertIsNone(r["glyph_label"])
        self.assertNotEqual(r["roi_mm"], vrm.SCAFFOLD_PLACEHOLDER_ROI)

    def test_a_scaffolded_manifest_is_rejected_until_filled(self):
        import run_real_batch as rrb
        caps = os.path.join(self.tmp, "caps", "P01", "A", "OP1", "R1")
        os.makedirs(caps)
        open(os.path.join(caps, "f1.png"), "wb").close()
        out = os.path.join(self.tmp, "scaffold.json")
        buf, old = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            rrb.scaffold(os.path.join(self.tmp, "caps"), out)
        finally:
            sys.stdout = old
        issues, _s, _c = check(load_json(out))
        self.assertIn("GLYPH_NOT_PREREGISTERED", codes(issues))

    def test_cli_honours_the_gate_policy_hull_margin(self):
        g = glyph()
        p = os.path.join(self.tmp, "m.json")
        dump_json(p, manifest_for(run_for(g, roi=filled_roi(g))))
        rc, _txt = self._cli(["--manifest", p, "--gate-policy", GATE_POLICY])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
