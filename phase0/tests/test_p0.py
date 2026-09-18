"""P0-min test suite (stdlib unittest; run with `python3 -m unittest discover tests`).

The tests are the falsifiability harness for the pipeline itself:
ground truth in the synthetic renderer is exact, so any arithmetic error shows up
as a numeric failure rather than as a plausible-looking measurement.
"""
from __future__ import annotations

import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from p0.camera import (Camera, homography_for_plane, jacobian,  # noqa: E402
                       plane_to_distorted_px, pose_looking_at_origin, rho_at,
                       view_tilt_deg, z_estimate_mm)
from p0.core import (Img, Rng, apply_h, load_json, lstsq, mat3_inv,  # noqa: E402
                     mat3_mul, obj_hash, percentile, solve, srgb_encode,
                     SRGB_DECODE, write_png_gray, read_png_gray, seed_from)
from p0.fiducial import DICTIONARY, detect_frame, DetectError  # noqa: E402
from p0.gates import default_gate_policy, evaluate, status_from  # noqa: E402
from p0.geometry import (fit_homography, hull_margin_mm,  # noqa: E402
                         leave_one_group_out_scale, reprojection_stats)
from p0.pipeline import measure_run                            # noqa: E402
from p0.render import (SceneSpec, glyph_bbox_mm, glyph_ink_at,   # noqa: E402
                       glyph_sdf, glyph_shape_class, render_burst,
                       render_frame, true_ink_height_mm)
from p0.uncertainty import (build_budget, decide, default_model,  # noqa: E402
                            thickness_correction)

CFG = os.path.join(ROOT, "config")


def cfg(*parts):
    return load_json(os.path.join(CFG, *parts))


class TestLinAlg(unittest.TestCase):
    def test_solve(self):
        A = [[2.0, 1.0, -1.0], [-3.0, -1.0, 2.0], [-2.0, 1.0, 2.0]]
        b = [8.0, -11.0, -3.0]
        x = solve(A, b)
        for got, want in zip(x, [2.0, 3.0, -1.0]):
            self.assertAlmostEqual(got, want, places=9)

    def test_lstsq_exact(self):
        rows = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        rhs = [1.0, 2.0, 3.0]
        x = lstsq(rows, rhs)
        self.assertAlmostEqual(x[0], 1.0, places=9)
        self.assertAlmostEqual(x[1], 2.0, places=9)

    def test_mat3_inv(self):
        M = [[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]]
        I = mat3_mul(M, mat3_inv(M))
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(I[i][j], 1.0 if i == j else 0.0, places=9)

    def test_singular_raises(self):
        with self.assertRaises(ZeroDivisionError):
            solve([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])


class TestSrgb(unittest.TestCase):
    def test_roundtrip(self):
        for v in range(0, 256, 7):
            lin = SRGB_DECODE[v]
            self.assertAlmostEqual(srgb_encode(lin) * 255.0, v, places=4)

    def test_not_affine(self):
        """The reason linearisation matters: midpoints do not correspond."""
        lo, hi = SRGB_DECODE[20], SRGB_DECODE[210]
        mid_lin = 0.5 * (lo + hi)
        mid_enc = SRGB_DECODE[(20 + 210) // 2]
        self.assertGreater(abs(mid_lin - mid_enc), 0.05)


class TestRng(unittest.TestCase):
    def test_deterministic(self):
        a = [Rng(42).normal() for _ in range(1)]
        b = [Rng(42).normal() for _ in range(1)]
        self.assertEqual(a, b)
        self.assertNotEqual(Rng(42).next_u64(), Rng(43).next_u64())

    def test_seed_from_stable(self):
        self.assertEqual(seed_from("a", 1), seed_from("a", 1))


class TestPng(unittest.TestCase):
    def test_roundtrip(self):
        img = Img(9, 5, 0.0)
        for i in range(45):
            img.lin[i] = SRGB_DECODE[(i * 5) % 256]
        path = os.path.join(ROOT, "out", "_test.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_png_gray(path, 9, 5, img.quantize_u8())
        back = read_png_gray(path)
        self.assertEqual((back.w, back.h), (9, 5))
        for i in range(45):
            self.assertAlmostEqual(back.lin[i], img.lin[i], places=6)
        os.remove(path)


class TestCameraGeometry(unittest.TestCase):
    def setUp(self):
        self.cam = Camera.from_dict(cfg("cameras", "CAM-SYN-A.json")["camera"])

    def test_distortion_roundtrip(self):
        cam = Camera.from_dict(cfg("cameras", "CAM-SYN-A-DIST.json")["camera"])
        for x in (-0.25, 0.0, 0.18):
            for y in (-0.2, 0.05, 0.22):
                xd, yd = cam.distort_norm(x, y)
                xr, yr = cam.undistort_norm(xd, yd)
                self.assertAlmostEqual(xr, x, places=9)
                self.assertAlmostEqual(yr, y, places=9)

    def test_fronto_parallel_scale(self):
        R, t = pose_looking_at_origin(200.0, 0.0)
        H = homography_for_plane(self.cam, R, t)
        rho, _, ratio = rho_at(H, 0.0, 0.0)
        self.assertAlmostEqual(rho, self.cam.f_px / 200.0, places=6)
        self.assertAlmostEqual(ratio, 1.0, places=6)
        self.assertAlmostEqual(view_tilt_deg(self.cam, H), 0.0, places=4)
        self.assertAlmostEqual(z_estimate_mm(self.cam, H, 0.0, 0.0), 200.0, places=4)

    def test_tilt_recovered(self):
        for tilt in (10.0, 25.0, 40.0):
            R, t = pose_looking_at_origin(200.0, tilt)
            H = homography_for_plane(self.cam, R, t)
            self.assertAlmostEqual(view_tilt_deg(self.cam, H), tilt, places=3)

    def test_origin_projects_to_principal_point(self):
        R, t = pose_looking_at_origin(220.0, 18.0, azimuth_deg=12.0)
        H = homography_for_plane(self.cam, R, t)
        u, v = apply_h(H, 0.0, 0.0)
        self.assertAlmostEqual(u, self.cam.cx, places=4)
        self.assertAlmostEqual(v, self.cam.cy, places=4)

    def test_plane_offset_scale_ratio(self):
        """Offsetting the print plane by d changes scale by d/Z to first order."""
        R, t = pose_looking_at_origin(200.0, 0.0)
        H0 = homography_for_plane(self.cam, R, t, 0.0)
        Hd = homography_for_plane(self.cam, R, t, 2.0)
        r0, _, _ = rho_at(H0, 0.0, 0.0)
        rd, _, _ = rho_at(Hd, 0.0, 0.0)
        self.assertAlmostEqual(rd / r0, 200.0 / 198.0, places=6)

    def test_jacobian_matches_finite_difference(self):
        R, t = pose_looking_at_origin(200.0, 20.0)
        H = homography_for_plane(self.cam, R, t)
        J = jacobian(H, 5.0, -3.0)
        e = 1e-4
        u1, v1 = apply_h(H, 5.0 + e, -3.0)
        u0, v0 = apply_h(H, 5.0 - e, -3.0)
        self.assertAlmostEqual(J[0][0], (u1 - u0) / (2 * e), places=3)
        self.assertAlmostEqual(J[1][0], (v1 - v0) / (2 * e), places=3)


class TestHomographyFit(unittest.TestCase):
    def test_recovers_known_homography(self):
        cam = Camera.from_dict(cfg("cameras", "CAM-SYN-A.json")["camera"])
        R, t = pose_looking_at_origin(210.0, 22.0, azimuth_deg=8.0, roll_deg=3.0)
        H = homography_for_plane(cam, R, t)
        plane = [(-40, 22), (40, 22), (40, -22), (-40, -22), (0, 0), (20, -10)]
        img = [apply_h(H, x, y) for x, y in plane]
        Hf = fit_homography(plane, img)
        for (x, y) in [(0, 0), (15, 8), (-30, -15)]:
            a = apply_h(H, x, y)
            b = apply_h(Hf, x, y)
            self.assertAlmostEqual(a[0], b[0], places=5)
            self.assertAlmostEqual(a[1], b[1], places=5)
        st = reprojection_stats(Hf, plane, img)
        self.assertLess(st["rms_px"], 1e-5)

    def test_lomo_zero_for_perfect_points(self):
        cam = Camera.from_dict(cfg("cameras", "CAM-SYN-A.json")["camera"])
        R, t = pose_looking_at_origin(200.0, 0.0)
        H = homography_for_plane(cam, R, t)
        plane, groups = [], []
        for gi, (cx, cy) in enumerate([(-40, 22), (40, 22), (40, -22), (-40, -22)]):
            for dx, dy in ((-5, 5), (5, 5), (5, -5), (-5, -5)):
                plane.append((cx + dx, cy + dy))
                groups.append(gi)
        img = [apply_h(H, x, y) for x, y in plane]
        out = leave_one_group_out_scale(plane, img, groups, (0.0, 0.0))
        self.assertEqual(out["n_fits"], 4)
        self.assertLess(out["rel_spread"], 1e-9)

    def test_hull_margin(self):
        pts = [(-40, 22), (40, 22), (40, -22), (-40, -22)]
        self.assertAlmostEqual(hull_margin_mm((0.0, 0.0), pts), 22.0, places=6)
        self.assertLess(hull_margin_mm((50.0, 0.0), pts), 0.0)


class TestRenderGroundTruth(unittest.TestCase):
    def test_true_height_is_exact_for_every_shape(self):
        """Verify {sdf < spread} really has height design + 2*spread."""
        for shape in ("BAR_I", "H", "T", "RING_O"):
            for h in (2.0, 3.0, 6.0):
                for spread in (0.0, 0.05):
                    want = true_ink_height_mm(shape, h, spread)
                    top = _ink_extreme(shape, h, spread, +1)
                    bot = _ink_extreme(shape, h, spread, -1)
                    self.assertAlmostEqual(top - bot, want, delta=2e-6,
                                           msg="%s h=%s spread=%s" % (shape, h, spread))

    def test_bbox_contains_ink(self):
        for shape in ("BAR_I", "H", "T", "RING_O"):
            w, h = glyph_bbox_mm(shape, 3.0, 0.03)
            self.assertLess(glyph_sdf(shape, 0.0, 0.0, 3.0) - 0.03, w)
            self.assertAlmostEqual(h, 3.06, places=6)

    def test_shape_class_mapping(self):
        self.assertEqual(glyph_shape_class("BAR_I"), "FLAT_TOP")
        self.assertEqual(glyph_shape_class("RING_O"), "ROUND")


def _row_has_ink(shape, h, spread, y, samples=241):
    for i in range(samples):
        x = (-0.6 + 1.2 * i / (samples - 1.0)) * h
        if glyph_ink_at(shape, x, y, h, spread):
            return True
    return False


def _ink_extreme(shape, h, spread, sign):
    """Bisect the outermost y that still contains ink (test-side ground truth)."""
    inside = 0.0
    outside = sign * h
    assert _row_has_ink(shape, h, spread, inside)  # origin row must be ink
    for _ in range(60):
        mid = 0.5 * (inside + outside)
        if _row_has_ink(shape, h, spread, mid):
            inside = mid
        else:
            outside = mid
        if abs(outside - inside) < 1e-9:
            break
    return 0.5 * (inside + outside)


class TestFiducialDictionary(unittest.TestCase):
    def test_codes_are_rotation_distinct(self):
        from p0.fiducial import _hamming, _rot90
        self.assertGreaterEqual(len(DICTIONARY), 8)
        for i, a in enumerate(DICTIONARY):
            rots = [a]
            for _ in range(3):
                rots.append(_rot90(rots[-1]))
            for r in rots[1:]:
                self.assertGreaterEqual(_hamming(a, r), 6)
            for j, b in enumerate(DICTIONARY):
                if i == j:
                    continue
                for r in rots:
                    self.assertGreaterEqual(_hamming(r, b), 6)


class TestEndToEndSynthetic(unittest.TestCase):
    """T-01 style acceptance tests on exactly known geometry."""

    @classmethod
    def setUpClass(cls):
        cls.cert = cfg("frames", "FRAME-SYN-0001.json")
        cls.prof = cfg("cameras", "CAM-SYN-A.json")
        cls.cam = Camera.from_dict(cls.prof["camera"])
        cls.mp = cfg("measurand_policy_v1.json")
        cls.gp = cfg("gate_policy_v1.json")
        cls.um = cfg("uncertainty_model_v1.json")

    def _run(self, spec, n=3, threshold=None, gp=None, cert=None, cam=None):
        cert = cert or self.cert
        cam = cam or self.cam
        frames, gts = render_burst(cam, cert, spec, "T-" + obj_hash(spec.to_dict())[:12],
                                   n=n)
        gt = gts[0]
        roi = tuple(gt["glyph_center_mm"]) + tuple(gt["glyph_bbox_mm"])
        res = measure_run(frames, cam, cert, self.mp, gp or self.gp, self.um, roi,
                          gt["shape_class"],
                          threshold if threshold is not None
                          else 0.9 * gt["true_ink_height_mm"],
                          "TEST", context={"profile_id": self.prof["profile_id"],
                                           "z_calib_mm": self.prof["z_calib_mm"]})
        return res, gt

    def test_T01_ideal_accuracy(self):
        for shape in ("BAR_I", "RING_O"):
            spec = SceneSpec(glyph_shape=shape, design_h_mm=3.0, blur_sigma_px=0.0,
                             noise_sigma=0.0, ink_spread_mm=0.0, jitter_pos_mm=0.0,
                             jitter_ang_deg=0.0, jitter_z_mm=0.0, ss_marker=6,
                             ss_glyph=8)
            res, gt = self._run(spec, n=2)
            self.assertEqual(res["status"], "MEASURED", res.get("reason_codes"))
            err = res["measurement"]["h_mm"] - gt["true_ink_height_mm"]
            self.assertLess(abs(err), 0.010, "%s err=%.5f" % (shape, err))

    def test_T09_missing_marker_hard_fails(self):
        spec = SceneSpec(glyph_shape="BAR_I", design_h_mm=3.0, drop_markers=(1,),
                         ss_marker=4, ss_glyph=4)
        res, _ = self._run(spec, n=2)
        self.assertTrue(res["status"].startswith("PHYSICAL_SIZE_NOT_ESTABLISHED"))
        self.assertIn("FIDUCIAL_MISSING_MARKER", res["reason_codes"])

    def test_T09_wrong_frame_hard_fails(self):
        spec = SceneSpec(glyph_shape="BAR_I", design_h_mm=3.0,
                         marker_ids=[4, 5, 6, 7], ss_marker=4, ss_glyph=4)
        res, _ = self._run(spec, n=2)
        self.assertTrue(res["status"].startswith("PHYSICAL_SIZE_NOT_ESTABLISHED"))

    def test_T11_gate_invariant_no_number_when_abstaining(self):
        spec = SceneSpec(glyph_shape="BAR_I", design_h_mm=3.0, ink_reflect=0.60,
                         ss_marker=4, ss_glyph=4)
        res, _ = self._run(spec, n=2)
        self.assertNotEqual(res["status"], "MEASURED")
        for key in ("h_mm", "lower_mm", "upper_mm", "decision"):
            self.assertIsNone(res["measurement"][key])

    def test_T08_plane_offset_matches_first_order_prediction(self):
        """d/Z scale error: measured bias must match theory within 15%."""
        d = 4.0
        spec = SceneSpec(glyph_shape="BAR_I", design_h_mm=3.0,
                         glyph_plane_offset_mm=d, ss_marker=5, ss_glyph=6,
                         jitter_pos_mm=0.0, jitter_ang_deg=0.0, jitter_z_mm=0.0)
        res, gt = self._run(spec, n=2)
        self.assertEqual(res["status"], "MEASURED")
        true = gt["true_ink_height_mm"]
        err = res["measurement"]["h_mm"] - true
        predicted = true * d / 200.0
        self.assertLess(abs(err - predicted), 0.15 * abs(predicted) + 0.005,
                        "err=%.4f predicted=%.4f" % (err, predicted))

    def test_T08_local_tilt_matches_cosine_prediction(self):
        alpha = 15.0
        spec = SceneSpec(glyph_shape="BAR_I", design_h_mm=3.0,
                         glyph_plane_tilt_deg=alpha, ss_marker=5, ss_glyph=6,
                         jitter_pos_mm=0.0, jitter_ang_deg=0.0, jitter_z_mm=0.0)
        res, gt = self._run(spec, n=2)
        self.assertEqual(res["status"], "MEASURED")
        true = gt["true_ink_height_mm"]
        err = res["measurement"]["h_mm"] - true
        predicted = -true * (1.0 - math.cos(math.radians(alpha)))
        self.assertLess(abs(err - predicted), 0.2 * abs(predicted) + 0.005,
                        "err=%.4f predicted=%.4f" % (err, predicted))

    def test_thickness_correction_recovers_declared_offset(self):
        cert = cfg("frames", "FRAME-SYN-0002-THICK.json")
        spec = SceneSpec(glyph_shape="BAR_I", design_h_mm=3.0,
                         glyph_plane_offset_mm=-cert["thickness_mm"],
                         ss_marker=5, ss_glyph=6)
        res, gt = self._run(spec, n=2, cert=cert)
        self.assertEqual(res["status"], "MEASURED")
        err = res["measurement"]["h_mm"] - gt["true_ink_height_mm"]
        self.assertLess(abs(err), 0.010, "err=%.5f" % err)

    def test_focal_length_error_does_not_bias_height(self):
        """A-08: metric scale comes from the surveyed fiducial, not from fx."""
        spec = SceneSpec(glyph_shape="BAR_I", design_h_mm=3.0, ss_marker=5,
                         ss_glyph=6, jitter_pos_mm=0.0, jitter_ang_deg=0.0,
                         jitter_z_mm=0.0)
        frames, gts = render_burst(self.cam, self.cert, spec, "FXTEST", n=2)
        gt = gts[0]
        roi = tuple(gt["glyph_center_mm"]) + tuple(gt["glyph_bbox_mm"])
        heights = []
        for scale in (0.90, 1.00, 1.10):
            d = dict(self.prof["camera"])
            d["fx"] = d["fx"] * scale
            d["fy"] = d["fy"] * scale
            cam = Camera.from_dict(d)
            res = measure_run(frames, cam, self.cert, self.mp, self.gp, self.um,
                              roi, gt["shape_class"],
                              0.9 * gt["true_ink_height_mm"], "FXTEST",
                              context={"profile_id": "p", "z_calib_mm": None})
            self.assertEqual(res["status"], "MEASURED", res.get("reason_codes"))
            heights.append(res["measurement"]["h_mm"])
        spread = max(heights) - min(heights)
        self.assertLess(spread, 0.005,
                        "20%% focal-length swing moved the height by %.5f mm" % spread)

    def test_T14_determinism(self):
        spec = SceneSpec(glyph_shape="BAR_I", design_h_mm=3.0, ss_marker=4,
                         ss_glyph=4)
        a, _ = self._run(spec, n=2)
        b, _ = self._run(spec, n=2)
        self.assertEqual(a["measurement"]["h_mm"], b["measurement"]["h_mm"])
        self.assertEqual(a["budget"]["u_c_mm"], b["budget"]["u_c_mm"])

    def test_estimator_beats_max_minus_min_under_noise(self):
        spec = SceneSpec(glyph_shape="BAR_I", design_h_mm=3.0, noise_sigma=0.02,
                         blur_sigma_px=0.8, ss_marker=5, ss_glyph=6)
        res, gt = self._run(spec, n=3)
        if res["status"] != "MEASURED":
            self.skipTest("gates abstained: %s" % res["reason_codes"])
        true = gt["true_ink_height_mm"]
        fit_err = abs(res["measurement"]["h_mm"] - true)
        mm = [f["h_maxminus_min_diagnostic_mm"] for f in res["per_frame"]]
        mm_err = abs(sum(mm) / len(mm) - true)
        self.assertLessEqual(fit_err, mm_err + 1e-9,
                             "fit=%.4f maxmin=%.4f" % (fit_err, mm_err))


class TestUncertainty(unittest.TestCase):
    def test_thickness_correction_sign(self):
        h, rel = thickness_correction(3.0, 0.5, 200.0)
        self.assertGreater(h, 3.0)
        self.assertAlmostEqual(rel, 0.0025, places=9)
        h2, rel2 = thickness_correction(3.0, 0.0, 200.0)
        self.assertEqual((h2, rel2), (3.0, 0.0))

    def test_budget_terms_combine(self):
        geom = {"lomo_rel_spread": 0.002, "z_mm": 200.0,
                "control_baseline_mm": 90.0}
        cert = {"thickness_u_mm": 0.01, "control_point_u_mm": 0.02}
        b = build_budget([3.0, 3.01, 2.99], [0.01, 0.01, 0.01], [0.02, 0.02, 0.02],
                         geom, cert, default_model())
        self.assertGreater(b["u_c_mm"], b["u_random_mm"])
        self.assertAlmostEqual(b["h_raw_mean_mm"], 3.0, places=9)
        self.assertLess(b["lower_mm"], b["h_corrected_mm"])
        self.assertGreater(b["upper_mm"], b["h_corrected_mm"])

    def test_guard_band_three_outcomes(self):
        base = {"lower_mm": 0.0, "upper_mm": 0.0, "h_corrected_mm": 0.0}
        self.assertEqual(decide(dict(base, lower_mm=3.1, upper_mm=3.3), 3.0),
                         "MEETS_SCREENING_THRESHOLD")
        self.assertEqual(decide(dict(base, lower_mm=2.7, upper_mm=2.9), 3.0),
                         "POTENTIAL_UNDERSIZE")
        self.assertEqual(decide(dict(base, lower_mm=2.9, upper_mm=3.1), 3.0),
                         "REQUIRES_OFFICER_REVIEW_BORDERLINE")

    def test_bias_is_corrected_not_added(self):
        model = dict(default_model(), bias_mm=0.05)
        geom = {"lomo_rel_spread": 0.0, "z_mm": 200.0, "control_baseline_mm": 90.0}
        b = build_budget([3.0, 3.0, 3.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0],
                         geom, {}, model)
        self.assertAlmostEqual(b["h_corrected_mm"], 2.95, places=9)


class TestGates(unittest.TestCase):
    def test_monotonic_stop_and_skip(self):
        gp = default_gate_policy()
        ctx = {"profile_id": "p", "camera_identity_match": True,
               "frame_serial_match": True, "frame_not_expired": True,
               "n_control_points": 4, "edge_rms_px": 0.1}
        g = evaluate(gp, ctx)
        status, reasons = status_from(g)
        self.assertTrue(status.startswith("PHYSICAL_SIZE_NOT_ESTABLISHED_FIDUCIAL"))
        self.assertEqual(g.failed[1], "control_points")
        self.assertTrue(any(r["evaluated"] is False for r in g.rows))

    def test_nan_fails_closed(self):
        gp = default_gate_policy()
        g = evaluate(gp, {"profile_id": "p", "camera_identity_match": True,
                          "frame_serial_match": True, "frame_not_expired": True,
                          "n_control_points": 16, "edge_rms_px": float("nan")})
        self.assertEqual(g.failed[1], "edge_fit_rms_px")

    def test_null_limit_disables_gate(self):
        gp = default_gate_policy()
        self.assertIsNone(gp["max_interval_width_mm"])
        g = evaluate(gp, {"interval_width_mm": 99.0})
        rows = [r for r in g.rows if r["gate"] == "interval_width_mm"]
        self.assertEqual(rows[0]["evaluated"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
