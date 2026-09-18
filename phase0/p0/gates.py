"""Monotonic gate evaluation and the MEASURE / ABSTAIN state machine.

Every gate reports value, limit and pass/fail, and gates after the first failure
are recorded as `evaluated: false` so the audit trail shows exactly how far the
run progressed.  A failed gate always yields a `PHYSICAL_SIZE_NOT_ESTABLISHED_*`
status and no numeric height (enforced by test_gate_invariants).
"""
from __future__ import annotations

import math

STAGES = ("PROFILE", "FIDUCIAL", "IMAGE_QUALITY", "GEOMETRY", "PLANARITY",
          "SEGMENTATION", "BURST", "UNCERTAINTY")

ABSTAIN_PREFIX = "PHYSICAL_SIZE_NOT_ESTABLISHED_"


def default_gate_policy():
    return {
        "policy_id": "GP-v2",
        # fiducial
        "min_control_points": 12,
        "max_edge_rms_px": 0.60,
        # image quality
        "max_blur_sigma_mm": 0.06,
        "min_michelson_contrast": 0.30,
        "min_snr": 20.0,
        "max_clip_dark_frac": 0.005,
        "max_clip_bright_frac": 0.005,
        "max_overshoot_ratio": 0.08,
        # geometry
        "max_reproj_rms_px": 0.25,
        "max_reproj_max_px": 0.60,
        "min_rho_px_per_mm": 10.0,
        "max_jacobian_ratio": 3.0,
        "min_hull_margin_mm": 8.0,
        "z_tolerance_frac": 0.35,
        "max_view_tilt_deg": 30.0,
        "max_lomo_rel_spread": 0.005,
        # planarity (fixture controlled, see A-06)
        "max_thickness_over_z": 0.01,
        # segmentation
        "min_scanline_fraction": 0.50,
        "max_median_crossings": 4,
        "max_sensitivity_dev_frac": 0.05,
        "min_cluster_points": 4,
        # Added in gate policy v2 after run v1 measured a ragged (dithered)
        # boundary without abstaining.  Derived from the expected edge
        # localisation noise (~0.3 px at rho >= 10 px/mm), not fitted to data.
        "max_edge_fit_rms_mm": 0.030,
        # burst
        "max_burst_sd_mm": 0.06,
        # uncertainty: null disables the gate until the model is calibrated
        "max_interval_width_mm": None,
        "max_interval_width_frac_of_threshold": None,
    }


class GateTable:
    def __init__(self):
        self.rows = []
        self.failed = None

    def add(self, stage, name, value, limit, ok, mode="max"):
        self.rows.append({"stage": stage, "gate": name, "value": value,
                          "limit": limit, "mode": mode, "passed": bool(ok),
                          "evaluated": True})
        if not ok and self.failed is None:
            self.failed = (stage, name)

    def skip(self, stage, name):
        self.rows.append({"stage": stage, "gate": name, "value": None,
                          "limit": None, "mode": None, "passed": None,
                          "evaluated": False})

    def check_max(self, stage, name, value, limit):
        if limit is None:
            self.rows.append({"stage": stage, "gate": name, "value": value,
                              "limit": None, "mode": "max", "passed": None,
                              "evaluated": False})
            return
        ok = value is not None and value == value and value <= limit
        self.add(stage, name, value, limit, ok, "max")

    def check_min(self, stage, name, value, limit):
        if limit is None:
            self.rows.append({"stage": stage, "gate": name, "value": value,
                              "limit": None, "mode": "min", "passed": None,
                              "evaluated": False})
            return
        ok = value is not None and value == value and value >= limit
        self.add(stage, name, value, limit, ok, "min")

    def as_dict(self):
        return {"rows": self.rows,
                "failed_stage": self.failed[0] if self.failed else None,
                "failed_gate": self.failed[1] if self.failed else None}


def evaluate(gp, ctx):
    """Evaluate all gates from an aggregated context dictionary."""
    g = GateTable()

    # ---- PROFILE --------------------------------------------------------
    g.add("PROFILE", "camera_profile_present", ctx.get("profile_id"), "not null",
          bool(ctx.get("profile_id")), "bool")
    g.add("PROFILE", "camera_identity_match", ctx.get("camera_identity_match"),
          True, bool(ctx.get("camera_identity_match")), "bool")
    g.add("PROFILE", "frame_serial_match", ctx.get("frame_serial_match"), True,
          bool(ctx.get("frame_serial_match")), "bool")
    g.add("PROFILE", "frame_not_expired", ctx.get("frame_not_expired"), True,
          bool(ctx.get("frame_not_expired")), "bool")

    # ---- FIDUCIAL -------------------------------------------------------
    g.check_min("FIDUCIAL", "control_points", ctx.get("n_control_points"),
                gp["min_control_points"])
    g.check_max("FIDUCIAL", "edge_fit_rms_px", ctx.get("edge_rms_px"),
                gp["max_edge_rms_px"])

    # ---- IMAGE QUALITY --------------------------------------------------
    g.check_max("IMAGE_QUALITY", "blur_sigma_mm", ctx.get("blur_sigma_mm"),
                gp["max_blur_sigma_mm"])
    g.check_min("IMAGE_QUALITY", "michelson_contrast", ctx.get("michelson_contrast"),
                gp["min_michelson_contrast"])
    g.check_min("IMAGE_QUALITY", "snr", ctx.get("snr"), gp["min_snr"])
    g.check_max("IMAGE_QUALITY", "clip_dark_frac", ctx.get("clip_dark_frac"),
                gp["max_clip_dark_frac"])
    g.check_max("IMAGE_QUALITY", "clip_bright_frac", ctx.get("clip_bright_frac"),
                gp["max_clip_bright_frac"])
    g.check_max("IMAGE_QUALITY", "overshoot_ratio", ctx.get("overshoot_ratio"),
                gp["max_overshoot_ratio"])

    # ---- GEOMETRY -------------------------------------------------------
    g.check_max("GEOMETRY", "reproj_rms_px", ctx.get("reproj_rms_px"),
                gp["max_reproj_rms_px"])
    g.check_max("GEOMETRY", "reproj_max_px", ctx.get("reproj_max_px"),
                gp["max_reproj_max_px"])
    g.check_min("GEOMETRY", "rho_min_px_per_mm", ctx.get("rho_min_px_per_mm"),
                gp["min_rho_px_per_mm"])
    g.check_max("GEOMETRY", "jacobian_ratio", ctx.get("jacobian_ratio"),
                gp["max_jacobian_ratio"])
    g.check_min("GEOMETRY", "hull_margin_mm", ctx.get("hull_margin_mm"),
                gp["min_hull_margin_mm"])
    g.check_max("GEOMETRY", "view_tilt_deg", ctx.get("view_tilt_deg"),
                gp["max_view_tilt_deg"])
    g.check_max("GEOMETRY", "lomo_rel_spread", ctx.get("lomo_rel_spread"),
                gp["max_lomo_rel_spread"])
    zc = ctx.get("z_calib_mm")
    zm = ctx.get("z_mm")
    if zc and zm and zm == zm:
        dev = abs(zm - zc) / zc
        g.check_max("GEOMETRY", "z_deviation_frac", dev, gp["z_tolerance_frac"])
    else:
        g.skip("GEOMETRY", "z_deviation_frac")

    # ---- PLANARITY ------------------------------------------------------
    g.check_max("PLANARITY", "thickness_over_z", ctx.get("thickness_over_z"),
                gp["max_thickness_over_z"])
    g.add("PLANARITY", "declared_flat_surface", ctx.get("declared_flat"), True,
          bool(ctx.get("declared_flat")), "bool")

    # ---- SEGMENTATION ---------------------------------------------------
    g.check_min("SEGMENTATION", "scanline_fraction", ctx.get("scanline_fraction"),
                gp["min_scanline_fraction"])
    g.check_max("SEGMENTATION", "median_crossings", ctx.get("median_crossings"),
                gp["max_median_crossings"])
    g.check_max("SEGMENTATION", "sensitivity_dev_frac",
                ctx.get("sensitivity_dev_frac"), gp["max_sensitivity_dev_frac"])
    g.check_min("SEGMENTATION", "min_cluster_points",
                ctx.get("min_cluster_points"), gp["min_cluster_points"])
    g.check_max("SEGMENTATION", "edge_fit_rms_mm", ctx.get("edge_fit_rms_mm"),
                gp.get("max_edge_fit_rms_mm"))

    # ---- BURST ----------------------------------------------------------
    g.check_max("BURST", "burst_sd_mm", ctx.get("burst_sd_mm"), gp["max_burst_sd_mm"])

    # ---- UNCERTAINTY ----------------------------------------------------
    width_limit = gp.get("max_interval_width_mm")
    frac = gp.get("max_interval_width_frac_of_threshold")
    thr = ctx.get("threshold_mm")
    if frac is not None and thr:
        alt = frac * thr
        width_limit = alt if width_limit is None else min(width_limit, alt)
    g.check_max("UNCERTAINTY", "interval_width_mm", ctx.get("interval_width_mm"),
                width_limit)

    return g


def status_from(gate_table: GateTable):
    if gate_table.failed is None:
        return "MEASURED", []
    stage, name = gate_table.failed
    reasons = [ABSTAIN_PREFIX + stage, "GATE_" + name.upper()]
    return ABSTAIN_PREFIX + stage, reasons
