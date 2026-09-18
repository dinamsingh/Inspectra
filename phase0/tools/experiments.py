"""Deterministic definition of the P0-min synthetic experiment suite.

`safety_class` is pre-registered per fixture and drives the PASS/FAIL analysis:

  SAFE                  nominal conditions; the pipeline should MEASURE and the
                        error must stay inside the accuracy criteria.
  UNSAFE_DETECTABLE     a defect the gate set is designed to catch; the pipeline
                        MUST abstain.  Measuring it counts as unsafe acceptance.
  UNSAFE_UNDETECTABLE   a defect that a single view provably cannot detect (an
                        undeclared plane offset or a locally tilted print plane).
                        The pipeline will measure; the resulting error is
                        reported as a *fixture control* requirement, never as a
                        detection capability.
  DIAGNOSTIC            sweeps whose purpose is to characterise behaviour rather
                        than to pass or fail.
"""
from __future__ import annotations

BASE = dict(blur_sigma_px=0.8, noise_sigma=0.002, ink_spread_mm=0.03,
            ss_marker=6, ss_glyph=8)


def _fx(fid, experiment, safety_class, spec, threshold=None, variants=None,
        frame="FRAME-SYN-0001", camera="CAM-SYN-A", note=""):
    return {"fixture_id": fid, "experiment": experiment,
            "safety_class": safety_class, "spec": spec,
            "threshold_mode": threshold or "0.9xTRUE",
            "variants": variants or ["base"], "frame": frame, "camera": camera,
            "note": note}


def suite():
    out = []

    # --- E_MATH: exact geometry, no blur/noise/ink spread -----------------
    for shape in ("BAR_I", "H", "T", "RING_O"):
        for h in (2.0, 4.0):
            out.append(_fx("E_MATH-%s-%.1f" % (shape, h), "E_MATH", "SAFE",
                           dict(BASE, glyph_shape=shape, design_h_mm=h,
                                blur_sigma_px=0.0, noise_sigma=0.0,
                                ink_spread_mm=0.0, jitter_pos_mm=0.0,
                                jitter_ang_deg=0.0, jitter_z_mm=0.0),
                           note="pipeline arithmetic exactness"))

    # --- E_NOMINAL: realistic controlled capture --------------------------
    for shape in ("BAR_I", "RING_O"):
        for h in (1.5, 2.0, 3.0, 4.0, 6.0):
            out.append(_fx("E_NOMINAL-%s-%.1f" % (shape, h), "E_NOMINAL", "SAFE",
                           dict(BASE, glyph_shape=shape, design_h_mm=h)))

    # --- sweeps -----------------------------------------------------------
    for b in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0):
        out.append(_fx("E_BLUR-%.1f" % b, "E_BLUR", "DIAGNOSTIC",
                       dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                            blur_sigma_px=b)))
    for t in (0.0, 10.0, 20.0, 30.0, 40.0, 50.0):
        out.append(_fx("E_TILT-%.0f" % t, "E_TILT", "DIAGNOSTIC",
                       dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                            tilt_deg=t)))
    # The whole fiducial frame must stay inside the image, so with CAM-SYN-A the
    # sweep can only move to larger working distances (rho = f_px / Z).
    for z in (200.0, 240.0, 280.0, 340.0, 420.0):
        out.append(_fx("E_RHO-%.0f" % z, "E_RHO", "DIAGNOSTIC",
                       dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0, z_mm=z)))
    out.append(_fx("E_RHO-200-hires", "E_RHO", "DIAGNOSTIC",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0, z_mm=200.0),
                   camera="CAM-SYN-B-HIRES", note="rho = 24 px/mm"))
    for n in (0.0, 0.005, 0.012, 0.025):
        out.append(_fx("E_NOISE-%.3f" % n, "E_NOISE", "DIAGNOSTIC",
                       dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                            noise_sigma=n)))
    for s in (0.0, 0.03, 0.06, 0.12):
        out.append(_fx("E_INKSPREAD-%.2f" % s, "E_INKSPREAD", "SAFE",
                       dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                            ink_spread_mm=s),
                       note="ground truth includes the spread"))
    out.append(_fx("E_ILLUM-gradient", "E_ILLUM", "SAFE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        illum_gradient=0.6)))
    out.append(_fx("E_ILLUM-glare-mild", "E_ILLUM", "SAFE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        glare={"x_mm": 12.0, "y_mm": 6.0, "sigma_mm": 4.0,
                               "amp": 0.12})))

    # --- E_THICKNESS: declared fiducial thickness must be corrected -------
    out.append(_fx("E_THICKNESS-declared", "E_THICKNESS", "SAFE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        glyph_plane_offset_mm=-0.45),
                   frame="FRAME-SYN-0002-THICK",
                   note="markers 0.45 mm above the print, declared in the cert"))

    # --- E_DECISION: guard band around a fixed threshold ------------------
    for h in (2.40, 2.70, 2.85, 2.95, 3.05, 3.15, 3.30, 3.60):
        out.append(_fx("E_DECISION-%.2f" % h, "E_DECISION", "SAFE",
                       dict(BASE, glyph_shape="BAR_I", design_h_mm=h,
                            ink_spread_mm=0.0),
                       threshold="FIXED_3.0"))

    # --- ablations (same images, different processing) --------------------
    out.append(_fx("E_DISTORT-offaxis", "E_DISTORT", "DIAGNOSTIC",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        glyph_center_mm=(20.0, 7.0)),
                   camera="CAM-SYN-A-DIST",
                   variants=["undistort_on", "undistort_off"],
                   note="E3: is per-device intrinsic calibration necessary?"))
    out.append(_fx("E_LINEARIZE-nominal", "E_LINEARIZE", "DIAGNOSTIC",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0),
                   variants=["linear", "gamma", "gamma_glyph_only"],
                   note="E2: threshold in linear vs sRGB-encoded space"))

    # --- negatives the gates must catch ----------------------------------
    out.append(_fx("N_WRONG_FIDUCIAL", "N_NEGATIVE", "UNSAFE_DETECTABLE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        marker_ids=[4, 5, 6, 7])))
    out.append(_fx("N_MISSING_MARKER", "N_NEGATIVE", "UNSAFE_DETECTABLE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        drop_markers=(2,))))
    # Run v1 showed that a 0.07 mm dither is simply blurred away and measured
    # correctly, so the original single fixture tested nothing.  The pitch is now
    # swept; only pitches that actually corrupt the boundary are pre-registered
    # as UNSAFE_DETECTABLE.
    out.append(_fx("N_UNSTABLE_BOUNDARY-0.07", "E_HALFTONE", "DIAGNOSTIC",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        halftone_pitch_mm=0.07),
                   note="v1 evidence: blurred to a uniform tint, measured correctly"))
    for pitch in (0.15, 0.30, 0.50):
        out.append(_fx("N_UNSTABLE_BOUNDARY-%.2f" % pitch, "N_NEGATIVE",
                       "UNSAFE_DETECTABLE",
                       dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                            halftone_pitch_mm=pitch),
                       note="ragged boundary at %.2f mm dither pitch" % pitch))
    out.append(_fx("N_LOW_CONTRAST", "N_NEGATIVE", "UNSAFE_DETECTABLE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        ink_reflect=0.55)))
    out.append(_fx("N_EXCESS_PERSPECTIVE", "N_NEGATIVE", "UNSAFE_DETECTABLE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        tilt_deg=55.0)))
    out.append(_fx("N_MOTION_BLUR", "N_NEGATIVE", "UNSAFE_DETECTABLE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        blur_sigma_px=0.8, blur_sigma_px_y=4.0)))
    out.append(_fx("N_GLARE_SATURATION", "N_NEGATIVE", "UNSAFE_DETECTABLE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        glare={"x_mm": 0.0, "y_mm": 0.0, "sigma_mm": 2.5,
                               "amp": 0.95})))
    out.append(_fx("N_SHARPENING", "N_NEGATIVE", "UNSAFE_DETECTABLE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                        unsharp_amount=1.5, unsharp_radius_px=1.6)))
    out.append(_fx("N_TINY_TEXT", "N_NEGATIVE", "UNSAFE_DETECTABLE",
                   dict(BASE, glyph_shape="BAR_I", design_h_mm=0.8, z_mm=340.0)))

    # --- negatives a single view provably cannot detect -------------------
    for d in (1.5, 5.0):
        out.append(_fx("N_PLANE_OFFSET_UNDECLARED-%.1f" % d, "N_UNDETECTABLE",
                       "UNSAFE_UNDETECTABLE",
                       dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                            glyph_plane_offset_mm=d),
                       note="print plane %.1f mm off the fiducial plane" % d))
    for a in (10.0, 20.0):
        out.append(_fx("N_NONPLANAR_TILT-%.0f" % a, "N_UNDETECTABLE",
                       "UNSAFE_UNDETECTABLE",
                       dict(BASE, glyph_shape="BAR_I", design_h_mm=3.0,
                            glyph_plane_tilt_deg=a),
                       note="print patch tilted %.0f deg vs fiducial plane" % a))
    return out


def summary():
    s = suite()
    by = {}
    for f in s:
        by[f["experiment"]] = by.get(f["experiment"], 0) + 1
    runs = sum(len(f["variants"]) for f in s)
    return {"fixtures": len(s), "runs": runs, "by_experiment": by}


if __name__ == "__main__":
    import json
    print(json.dumps(summary(), indent=2, sort_keys=True))
