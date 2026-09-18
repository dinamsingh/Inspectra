"""Uncertainty budget and guard-band decision.

Design decisions (PHASE0_REVIEW F9.1 - F9.3, F10.1):

* The primary random term is **measured**, not modelled: the standard error of
  the mean over a repeated-capture burst.  `u_edge` (within-frame fit standard
  error) is used as a floor so a suspiciously quiet burst cannot claim an
  unrealistically small uncertainty.  The two are combined with `max`, not in
  quadrature, because they overlap.
* Bounded systematic effects enter as rectangular distributions (`a / sqrt(3)`),
  following the usual GUM treatment, rather than being added as if random.
* A bias is **corrected**, not absorbed into the uncertainty.  Only the
  uncertainty of the correction is combined.
* Scale, survey, thickness and residual-tilt terms are common mode across
  glyphs; the fit term is per glyph.  They are kept separate so a
  minimum-over-glyphs rule cannot double count the common part.
* `k_lower` / `k_upper` are explicit **one-sided** coverage factors.  The
  default 1.645 is the nominal Gaussian 95% value and is NOT validated; the
  experiment reports empirical coverage so the assumption can be falsified.
"""
from __future__ import annotations

import math

from .core import mean, sd

SQRT3 = math.sqrt(3.0)


def default_model():
    return {
        "model_version": "UM-v1-uncalibrated",
        "bias_mm": 0.0,
        "u_bias_correction_mm": 0.0,
        "u_extra_mm": 0.0,
        "k_lower": 1.645,
        "k_upper": 1.645,
        "residual_tilt_bound_deg": 3.0,
        "calibrated": False,
    }


def build_budget(h_frames, u_edge_frames, h_sens_dev_frames, geom, frame_cert,
                 model):
    """Combine the uncertainty budget for one measurement run."""
    n = len(h_frames)
    h_mean = mean(h_frames)
    burst_sd = sd(h_frames)
    u_burst = burst_sd / math.sqrt(n) if n > 1 else float("nan")
    u_edge_mean = mean([v for v in u_edge_frames if v == v]) if u_edge_frames else 0.0
    u_edge_floor = u_edge_mean / math.sqrt(n) if n > 0 else 0.0
    u_random = max(u_burst if u_burst == u_burst else 0.0, u_edge_floor)

    lomo = geom.get("lomo_rel_spread", float("nan"))
    u_scale = (h_mean * lomo / SQRT3) if lomo == lomo else float("nan")

    seg_dev = mean([v for v in h_sens_dev_frames if v == v]) if h_sens_dev_frames else 0.0
    u_seg = seg_dev / SQRT3

    z = geom.get("z_mm", float("nan"))
    thick_u = float(frame_cert.get("thickness_u_mm", 0.0))
    u_thick = (h_mean * thick_u / z / SQRT3) if z == z and z > 0 else 0.0

    baseline = geom.get("control_baseline_mm", float("nan"))
    survey_u = float(frame_cert.get("control_point_u_mm", 0.0))
    u_ref = (h_mean * survey_u / baseline / SQRT3) if baseline == baseline and baseline > 0 else 0.0

    tilt_bound = math.radians(float(model.get("residual_tilt_bound_deg", 0.0)))
    u_tilt = h_mean * (1.0 - math.cos(tilt_bound)) / SQRT3

    u_extra = float(model.get("u_extra_mm", 0.0))
    u_bias = float(model.get("u_bias_correction_mm", 0.0))

    common_terms = [u_scale if u_scale == u_scale else 0.0, u_seg, u_thick, u_ref,
                    u_tilt, u_extra, u_bias]
    u_common = math.sqrt(sum(v * v for v in common_terms))
    u_c = math.sqrt(u_random * u_random + u_common * u_common)

    h_corr = h_mean - float(model.get("bias_mm", 0.0))
    kl = float(model.get("k_lower", 1.645))
    ku = float(model.get("k_upper", 1.645))

    return {
        "n_frames": n,
        "h_raw_mean_mm": h_mean,
        "burst_sd_mm": burst_sd,
        "u_burst_mm": u_burst,
        "u_edge_floor_mm": u_edge_floor,
        "u_random_mm": u_random,
        "u_scale_mm": u_scale,
        "u_seg_mm": u_seg,
        "u_thickness_mm": u_thick,
        "u_ref_mm": u_ref,
        "u_tilt_mm": u_tilt,
        "u_extra_mm": u_extra,
        "u_bias_correction_mm": u_bias,
        "u_common_mm": u_common,
        "u_c_mm": u_c,
        "bias_correction_mm": float(model.get("bias_mm", 0.0)),
        "h_corrected_mm": h_corr,
        "k_lower": kl,
        "k_upper": ku,
        "lower_mm": h_corr - kl * u_c,
        "upper_mm": h_corr + ku * u_c,
        "interval_width_mm": (kl + ku) * u_c,
        "model_version": model.get("model_version"),
        "model_calibrated": bool(model.get("calibrated", False)),
    }


def thickness_correction(h_mm, thickness_mm, z_mm):
    """Correct for the fiducial plane sitting `thickness_mm` above the print.

    The markers are closer to the camera than the printed surface, so the scale
    derived from them under-estimates the print-plane height by d/Z.
    """
    if z_mm is None or z_mm != z_mm or z_mm <= 0.0 or thickness_mm == 0.0:
        return h_mm, 0.0
    factor = 1.0 + thickness_mm / z_mm
    return h_mm * factor, factor - 1.0


def decide(budget, threshold_mm):
    """Guard-band decision using explicit one-sided bounds."""
    if threshold_mm is None:
        return "NO_THRESHOLD_CONFIGURED"
    if budget["lower_mm"] >= threshold_mm:
        return "MEETS_SCREENING_THRESHOLD"
    if budget["upper_mm"] < threshold_mm:
        return "POTENTIAL_UNDERSIZE"
    return "REQUIRES_OFFICER_REVIEW_BORDERLINE"
