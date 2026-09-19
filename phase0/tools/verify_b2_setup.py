#!/usr/bin/env python3
"""Pre-capture gate for blocker B2: is the reference setup actually verified?

This tool does **not** measure anything and does **not** touch the measurement
algorithm.  It reads one hand-filled evidence file describing the instruments,
records, people and software that will produce the reference values, and returns a
single verdict:

    B2_SETUP_VERIFIED = YES | NO

The whole point is that **NO is the default**.  A field left blank, left as a
placeholder ("TBD", "UNSPECIFIED", ...), or naming a decision that is still open
produces NO.  Nothing is assumed to exist, and a missing calibration record can
never pass silently.

Every check traces to an existing frozen document.  No numeric specification is
invented here: 2400 dpi, 8-bit greyscale, the 1 % print-scale limit, the 0.01 mm
caliper resolution, the <= 0.01 mm reference-uncertainty target, the P1 bands and
the M1/M3/M4/S3 rules all come from `docs/P0_PROTOCOL.md`,
`docs/P0_CRITERIA.md`, `docs/P0_ASSUMPTIONS.md` and
`docs/P0_REFERENCE_PROCEDURE.md`.

Usage:
    python3 tools/verify_b2_setup.py --template reference/b2_setup.json
    python3 tools/verify_b2_setup.py --evidence reference/b2_setup.json
Exit code: 0 verified, 1 not verified, 2 could not load.
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.core import dump_json, load_json          # noqa: E402

MANDATORY, ADVISORY = "MANDATORY", "ADVISORY"

# Values that are not evidence.  `UNSPECIFIED` is included because
# `tools/survey_frame.py` uses it as its own "not answered" default.
PLACEHOLDERS = frozenset((
    "", "-", "?", "??", "n/a", "na", "tbd", "todo", "none", "null", "unknown",
    "unspecified", "pending", "xxx", "fill me", "fixme",
))

# docs/P0_PROTOCOL.md §0, §3: 2400 dpi optical, 8-bit greyscale
REQUIRED_OPTICAL_DPI = 2400
REQUIRED_BIT_DEPTH = 8
# docs/P0_ASSUMPTIONS.md A-02: the reader takes 8-bit grey PNG; the scan must
# therefore arrive in a format that converts without resampling or tone mapping.
LOSSLESS_FORMATS = ("PNG", "TIFF", "TIF", "BMP", "PPM", "PGM")
# docs/P0_PROTOCOL.md §1 step 1: more than 1 percent off means the printer is scaling
CHECK_BAR_NOMINAL_MM = 100.0
CHECK_BAR_TOLERANCE_FRAC = 0.01
# docs/P0_PROTOCOL.md §0: caliper resolution 0.01 mm
CALIPER_MAX_RESOLUTION_MM = 0.01
# docs/P0_PROTOCOL.md §3 step 4: reference uncertainty target
REFERENCE_U_TARGET_MM = 0.01
# docs/P0_CRITERIA.md P1 Go band, used only to report a share, never as a limit here
P1_GO_BAND_MM = 0.03
# docs/P0_EXECUTION_PLAN.md §1.2 / P0_PROTOCOL.md §0
REQUIRED_PANELS = 20
# docs/P0_REFERENCE_PROCEDURE.md §4.2.4
M1_MIN_REPEATS = 3
M1_RAW_FORMAT = "Obot/Ibot/Itop/Otop"

MICROSCOPE_TYPES = ("MEASURING_MICROSCOPE", "TOOLMAKERS_MICROSCOPE",
                    "USB_MICROSCOPE_WITH_CALIBRATION_SLIDE")
# PHASE0_REVIEW.md §15 lists the USB route as "acceptable secondary", not preferred.
MICROSCOPE_SECONDARY = ("USB_MICROSCOPE_WITH_CALIBRATION_SLIDE",)
STANDARD_TYPES = ("STEEL_SCALE", "GLASS_GRATICULE")

# Decisions that must be RESOLVED before any reference value is produced.  Each is
# named exactly as the owning document names it.
OPEN_DECISION_KEYS = (
    "S2_roi_rule", "S4_platen_rule", "S5_repeats_rule", "S6_baseline_rule",
    "M2_magnification_and_reading_resolution", "M5_operator_training",
    "C6_reference_population", "C9_cross_check_subset", "D1_disagreement_rule",
)
# Already frozen; carried in the file so the record is complete and so the reader
# can see what a resolved entry looks like.
SETTLED_DECISIONS = {
    "M1_edge_criterion": "RESOLVED: docs/P0_REFERENCE_PROCEDURE.md §4.2.3",
    "M3_baseline_realisation": "RESOLVED: docs/P0_REFERENCE_PROCEDURE.md §4.2.4",
    "M4_repeats_and_uncertainty": "RESOLVED: docs/P0_REFERENCE_PROCEDURE.md §4.2.4",
    "S3_frame_in_scan": "RESOLVED: NO - docs/P0_REFERENCE_PROCEDURE.md §3.2",
}


class SetupEvidenceError(Exception):
    pass


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def named(value):
    """True only if `value` is a real, non-placeholder string."""
    if not isinstance(value, str):
        return False
    return value.strip().lower() not in PLACEHOLDERS


def as_number(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and named(value):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def is_true(value):
    """Strictly true.  A string, a null or a missing key is NOT true."""
    return value is True


def get(evidence, section, key):
    sec = evidence.get(section)
    if not isinstance(sec, dict):
        return None
    return sec.get(key)


# ---------------------------------------------------------------------------
# the checks
# ---------------------------------------------------------------------------

def _scanner(ev, chk):
    s = "scanner"
    chk(MANDATORY, "SCANNER_IDENTIFIED", named(get(ev, s, "instrument_id")),
        "scanner instrument_id must name one physical unit; every panel must be "
        "scanned on that same unit")
    dpi = as_number(get(ev, s, "optical_dpi"))
    chk(MANDATORY, "SCANNER_OPTICAL_DPI", dpi is not None and dpi >= REQUIRED_OPTICAL_DPI,
        "optical_dpi must be >= %d (P0_PROTOCOL.md §0, §3). At 600 dpi one pixel "
        "is 0.0423 mm, larger than P1's whole Go band" % REQUIRED_OPTICAL_DPI)
    chk(MANDATORY, "SCANNER_DPI_IS_OPTICAL", is_true(get(ev, s, "dpi_is_optical")),
        "the figure must be the sensor's optical resolution, not an interpolated "
        "or marketing figure; interpolation adds no information")
    used = as_number(get(ev, s, "dpi_used_for_scan"))
    chk(MANDATORY, "SCANNER_SCANNED_AT_REQUIRED_DPI",
        used is not None and used >= REQUIRED_OPTICAL_DPI,
        "the scan itself must be taken at >= %d dpi, not downsampled afterwards"
        % REQUIRED_OPTICAL_DPI)
    chk(MANDATORY, "SCANNER_GREYSCALE_MODE",
        str(get(ev, s, "scan_mode") or "").strip().upper() in ("GREY", "GRAY",
                                                               "GREYSCALE", "GRAYSCALE"),
        "scan_mode must be greyscale (P0_PROTOCOL.md §3 step 2)")
    depth = as_number(get(ev, s, "bit_depth"))
    chk(MANDATORY, "SCANNER_BIT_DEPTH",
        depth is not None and depth >= REQUIRED_BIT_DEPTH,
        "bit_depth must be >= %d (P0_PROTOCOL.md §3 step 2, A-02)" % REQUIRED_BIT_DEPTH)
    disabled = get(ev, s, "enhancement_items_disabled")
    chk(MANDATORY, "SCANNER_ENHANCEMENT_OFF",
        is_true(get(ev, s, "enhancement_off")) and isinstance(disabled, list)
        and any(named(x) for x in disabled),
        "enhancement_off must be true AND enhancement_items_disabled must name "
        "what was switched off (sharpening, descreen, dust removal, auto tone, "
        "colour restoration). 'All off' with nothing named is not evidence")
    fmt = str(get(ev, s, "output_format") or "").strip().upper()
    chk(MANDATORY, "SCANNER_LOSSLESS_OUTPUT", fmt in LOSSLESS_FORMATS,
        "output_format must be one of %s. JPEG is rejected: A-02 forbids a "
        "conversion that applies sharpening or tone mapping" % (list(LOSSLESS_FORMATS),))
    chk(MANDATORY, "SCANNER_NO_RESAMPLING",
        get(ev, s, "resampling_or_rescaling") is False,
        "resampling_or_rescaling must be explicitly false; any rescale moves the "
        "ink boundary")
    chk(MANDATORY, "SCANNER_SINGLE_SESSION",
        is_true(get(ev, s, "single_session_all_panels")),
        "all panels must be scanned in one calibrated session on one unit. A "
        "second session on a different scanner splits the reference population "
        "across two uncalibrated scales, and the discontinuity is invisible in "
        "the data")
    chk(MANDATORY, "SCANNER_SCALE_CALIBRATED_IN_SESSION",
        named(get(ev, s, "scale_calibration_ref")),
        "the scanner's scale calibration against the certified standard must be "
        "recorded, and performed in the same session (P0_PROTOCOL.md §3 step 1)")
    sx = as_number(get(ev, s, "scale_factor_x"))
    sy = as_number(get(ev, s, "scale_factor_y"))
    chk(MANDATORY, "SCANNER_BOTH_AXES_CALIBRATED", sx is not None and sy is not None,
        "scale_factor_x and scale_factor_y must both be recorded; flatbed "
        "carriage-direction scale commonly differs from sensor-direction scale "
        "(P0_PROTOCOL.md §3 step 1 says both axes)")
    chk(MANDATORY, "SCANNER_PLATEN_NONUNIFORMITY_RECORDED",
        is_true(get(ev, s, "platen_nonuniformity_recorded")),
        "non-uniformity across the platen must be recorded (P0_PROTOCOL.md §3 "
        "step 1). Recording it is not the same as correcting it - see S4")
    chk(MANDATORY, "SCANNER_NO_FRAME_IN_SCAN",
        get(ev, s, "frame_in_scan") is False,
        "S3 is frozen as NO: the fiducial frame is not scanned with the coupon "
        "(docs/P0_REFERENCE_PROCEDURE.md §3.2)")
    if sx is not None and sy is not None and sx != 0:
        chk(ADVISORY, "SCANNER_AXIS_ANISOTROPY",
            abs(sy / sx - 1.0) <= 0.005,
            "x/y scale differ by %.3f %%; anisotropy is representable (fx != fy) "
            "but a large value is worth understanding before it becomes a "
            "reference value" % (100.0 * abs(sy / sx - 1.0)))


def _standard(ev, chk):
    s = "length_standard"
    chk(MANDATORY, "STANDARD_IDENTIFIED", named(get(ev, s, "standard_id")),
        "the certified length standard must be identified (P0_PROTOCOL.md §0)")
    chk(MANDATORY, "STANDARD_TYPE",
        str(get(ev, s, "type") or "").strip().upper() in STANDARD_TYPES,
        "type must be one of %s (P0_PROTOCOL.md §0: steel rule or glass "
        "graticule with a certificate)" % (list(STANDARD_TYPES),))
    chk(MANDATORY, "STANDARD_CERTIFICATE_REF", named(get(ev, s, "certificate_ref")),
        "a certificate reference is mandatory; it is what `instrument_cal_ref` "
        "records in the reference table. An uncertified ruler is NOT ACCEPTABLE")
    chk(MANDATORY, "STANDARD_CERTIFICATE_ISSUED", named(get(ev, s, "certificate_issued")),
        "the certificate issue date must be recorded, mirroring the frame "
        "certificate's `issued_at` (config/frames/*.json)")
    chk(MANDATORY, "STANDARD_TRACEABILITY", named(get(ev, s, "traceability")),
        "record what the certificate traces to, in the certificate's own words. "
        "No certification scheme is prescribed here")
    u = as_number(get(ev, s, "stated_uncertainty_mm"))
    chk(MANDATORY, "STANDARD_STATED_UNCERTAINTY", u is not None,
        "the certificate's stated uncertainty must be transcribed")
    chk(MANDATORY, "STANDARD_BOTH_AXES_VERIFIED",
        is_true(get(ev, s, "both_axes_verified")),
        "the standard must have been used to verify both scanner axes "
        "(P0_PROTOCOL.md §3 step 1)")
    expires = get(ev, s, "certificate_expires")
    chk(ADVISORY, "STANDARD_CERTIFICATE_EXPIRY_RECORDED", named(expires),
        "no expiry recorded. The repository's own frame certificates carry "
        "`expires_at`, so an expiry is expected where the certificate states one")
    if u is not None:
        chk(ADVISORY, "STANDARD_UNCERTAINTY_VS_TARGET", u <= REFERENCE_U_TARGET_MM,
            "the standard's own stated uncertainty (%.4f mm) is not below the "
            "reference-uncertainty target of %.2f mm (P0_PROTOCOL.md §3 step 4); "
            "the scanner tier cannot be better than its own scale reference"
            % (u, REFERENCE_U_TARGET_MM))


def _microscope(ev, chk):
    s = "microscope"
    mtype = str(get(ev, s, "type") or "").strip().upper()
    chk(MANDATORY, "MICROSCOPE_IDENTIFIED", named(get(ev, s, "instrument_id")),
        "the microscope must be identified; P1 cannot be computed without it, and "
        "without P1 no accuracy claim may be made at all")
    chk(MANDATORY, "MICROSCOPE_TYPE", mtype in MICROSCOPE_TYPES,
        "type must be one of %s. These are the classes PHASE0_REVIEW.md §15 "
        "actually lists" % (list(MICROSCOPE_TYPES),))
    chk(MANDATORY, "MICROSCOPE_XY_STAGE_READOUT",
        is_true(get(ev, s, "has_xy_stage_with_readout")),
        "M1 needs stage position readings, not just a magnified view. A viewer "
        "without a measuring stage cannot produce a reference value")
    chk(MANDATORY, "MICROSCOPE_STAGE_ROTATION",
        is_true(get(ev, s, "stage_rotation_available")),
        "M3 realises perpendicularity by rotating the stage until the baseline "
        "is parallel to X (docs/P0_REFERENCE_PROCEDURE.md §4.2.4)")
    res = as_number(get(ev, s, "reading_resolution_mm"))
    chk(MANDATORY, "MICROSCOPE_READING_RESOLUTION", res is not None and res > 0,
        "stage reading resolution must be stated. This is decision M2, and it "
        "cannot be answered by calling an instrument high-resolution")
    chk(MANDATORY, "MICROSCOPE_CALIBRATION_REF", named(get(ev, s, "calibration_ref")),
        "a calibration reference is mandatory; without it the reference value is "
        "not traceable (`instrument_cal_ref`)")
    chk(MANDATORY, "MICROSCOPE_REFLECTED_ILLUMINATION",
        str(get(ev, s, "illumination_mode") or "").strip().upper() == "REFLECTED",
        "M1 freezes reflected / episcopic illumination; transmitted light images "
        "the substrate, not the ink (docs/P0_REFERENCE_PROCEDURE.md §4.2.4)")
    chk(MANDATORY, "MICROSCOPE_M1_UNDERSTOOD",
        is_true(get(ev, s, "m1_procedure_read"))
        and is_true(get(ev, s, "m1_checklist_available")),
        "the operator must have read M1 (§4.2.3) and have the §4.2.6 checklist "
        "to hand before the first reading")
    chk(MANDATORY, "MICROSCOPE_OPERATOR_TRAINED",
        is_true(get(ev, s, "operator_trained_against_m1")),
        "decision M5: the operator must be trained against the written M1 "
        "criterion before the cross-check counts")
    rep = as_number(get(ev, s, "repeats_planned"))
    chk(MANDATORY, "MICROSCOPE_REPEATS_PLANNED",
        rep is not None and rep >= M1_MIN_REPEATS,
        "M4 sets a floor of %d independent re-settings per glyph" % M1_MIN_REPEATS)
    chk(MANDATORY, "MICROSCOPE_RAW_FORMAT",
        str(get(ev, s, "raw_reading_format") or "").strip() == M1_RAW_FORMAT,
        "raw_reading_format must be %r so the recorded value can be re-derived "
        "by tools/validate_reference_table.py" % M1_RAW_FORMAT)
    chk(ADVISORY, "MICROSCOPE_INTER_OPERATOR_CHECK",
        is_true(get(ev, s, "inter_operator_check_done")),
        "M5's second half: no inter-operator agreement check recorded, so "
        "operator-to-operator spread in the M1 judgement is unquantified")
    chk(ADVISORY, "MICROSCOPE_IS_PREFERRED_CLASS",
        mtype in MICROSCOPE_TYPES and mtype not in MICROSCOPE_SECONDARY,
        "PHASE0_REVIEW.md §15 lists this class as 'acceptable secondary' rather "
        "than preferred primary")
    if res is not None and res > 0:
        share = 100.0 * (res / 4.0) / P1_GO_BAND_MM
        chk(ADVISORY, "MICROSCOPE_QUANTISATION_SHARE_OF_P1", share <= 25.0,
            "a %.4f mm reading step contributes about %.4f mm to a mean absolute "
            "difference (d/4), i.e. %.1f %% of P1's %.2f mm Go band before any "
            "real disagreement is measured. Derived from the frozen band, not a "
            "limit" % (res, res / 4.0, share, P1_GO_BAND_MM))


def _caliper(ev, chk):
    s = "caliper"
    chk(MANDATORY, "CALIPER_IDENTIFIED", named(get(ev, s, "instrument_id")),
        "the caliper must be identified (frame survey and the 100 mm print check)")
    res = as_number(get(ev, s, "resolution_mm"))
    chk(MANDATORY, "CALIPER_RESOLUTION",
        res is not None and res <= CALIPER_MAX_RESOLUTION_MM,
        "resolution must be <= %.2f mm (P0_PROTOCOL.md §0)"
        % CALIPER_MAX_RESOLUTION_MM)
    chk(MANDATORY, "CALIPER_CALIBRATION_RECORD",
        named(get(ev, s, "calibration_record_ref")),
        "P0_PROTOCOL.md §0 requires a calibration record")
    chk(MANDATORY, "CALIPER_NOT_USED_AS_GLYPH_REFERENCE",
        get(ev, s, "used_for_glyph_reference") is False,
        "a caliper across a 3 mm printed glyph is 'never a reference' "
        "(P0_EXECUTION_PLAN.md §2.3); this must be explicitly false")


def _printing(ev, chk):
    s = "printing"
    chk(MANDATORY, "PRINTER_IDENTIFIED", named(get(ev, s, "printer_id")),
        "the printer used for the coupons must be identified")
    chk(MANDATORY, "PRINT_SCALE_VERIFIED",
        is_true(get(ev, s, "scale_verified_against_100mm_bar")),
        "the 100 mm check bar must have been measured (P0_PROTOCOL.md §1 step 1)")
    bar = as_number(get(ev, s, "measured_check_bar_mm"))
    ok = (bar is not None
          and abs(bar - CHECK_BAR_NOMINAL_MM)
          <= CHECK_BAR_TOLERANCE_FRAC * CHECK_BAR_NOMINAL_MM)
    chk(MANDATORY, "PRINT_SCALE_WITHIN_TOLERANCE", ok,
        "the measured check bar must be within %g %% of %.1f mm; beyond that "
        "P0_PROTOCOL.md §1 step 1 says the printer is scaling and must be fixed "
        "first" % (100 * CHECK_BAR_TOLERANCE_FRAC, CHECK_BAR_NOMINAL_MM))
    panels = as_number(get(ev, s, "coupon_panels_printed"))
    chk(MANDATORY, "COUPON_PANELS_PRINTED",
        panels is not None and panels >= REQUIRED_PANELS,
        "the frozen design is %d panels (P0_EXECUTION_PLAN.md §1.2); fewer is a "
        "design change, not a shortcut" % REQUIRED_PANELS)
    chk(MANDATORY, "COUPON_STOCK_DESCRIBED", named(get(ev, s, "stock_description")),
        "record the print stock; it is a documented variation factor")
    chk(MANDATORY, "COUPON_STOCK_STABLE",
        is_true(get(ev, s, "stock_dimensionally_stable")),
        "P0_PROTOCOL.md §0: dimensional stability matters more than print quality")
    chk(ADVISORY, "REAL_PRODUCTS_NOT_USED_AS_SAMPLE",
        get(ev, s, "real_packaged_products_used_as_p0_sample") is False,
        "real packaged products cannot serve as the P0 sample: they break the "
        "frozen nominal matrix, the flatness requirement (A-05/A-06) and B5")


def _people(ev, chk):
    s = "operators"
    so = get(ev, s, "scanner_operator")
    mo = get(ev, s, "microscope_operator")
    chk(MANDATORY, "OPERATORS_NAMED", named(so) and named(mo),
        "both operators must be named; `operator` is a mandatory reference-table "
        "field and supports the blinding rule")
    chk(MANDATORY, "MICROSCOPE_BLIND_TO_SCANNER_VALUES",
        is_true(get(ev, s, "microscope_blind_to_scanner_values")),
        "rule R6(b): the microscope operator must not have seen the scanner "
        "values for those glyphs. Simplest arrangement: microscope readings first")
    chk(ADVISORY, "OPERATORS_DISTINCT",
        named(so) and named(mo) and so.strip() != mo.strip(),
        "the same person is doing both methods. R6(c) is a *should*, so this is "
        "reported rather than rejected, but it will also show up per glyph as "
        "SAME_OPERATOR_BOTH_METHODS in the reference-table validator")


def _software(ev, chk):
    s = "software"
    chk(MANDATORY, "SCAN_MEASUREMENT_TOOL_EXISTS",
        named(get(ev, s, "scan_measurement_tool")),
        "blocker B2-1: a tool that measures a scan must exist and be named. Its "
        "route is fixed (dpi-derived pure-scale homography, no measurement-code "
        "change) but it is not written yet")
    chk(MANDATORY, "SCAN_MEASUREMENT_DRY_RUN",
        is_true(get(ev, s, "scan_measurement_dry_run_passed")),
        "the scan path must have been run end to end on a throwaway scan before "
        "the calibrated session; discovering this in the lab wastes the access")
    chk(MANDATORY, "PNG_CONVERSION_VERIFIED",
        is_true(get(ev, s, "png_conversion_verified_no_sharpening")),
        "A-02: the conversion to 8-bit grey PNG must be verified not to sharpen "
        "or tone map, and the command recorded")
    chk(MANDATORY, "REFERENCE_VALIDATOR_CLEAN",
        is_true(get(ev, s, "reference_validator_run_clean")),
        "tools/validate_reference_table.py must return ACCEPTED with 0 errors")
    chk(MANDATORY, "REFERENCE_TABLE_COMMITTED_FIRST",
        is_true(get(ev, s, "reference_table_committed_before_capture")),
        "the reference table is committed before the first camera capture "
        "(P0_EXECUTION_PLAN.md §6.3, §8)")


def _decisions(ev, chk):
    sec = ev.get("open_decisions")
    if not isinstance(sec, dict):
        sec = {}
    for key in OPEN_DECISION_KEYS:
        val = sec.get(key)
        resolved = named(val) and str(val).strip().upper().startswith("RESOLVED")
        chk(MANDATORY, "DECISION_" + key.upper(), resolved,
            "decision %s is not recorded as RESOLVED with a pointer; an "
            "undecided rule cannot be executed in a lab" % key)


CHECK_GROUPS = (
    ("scanner", _scanner),
    ("length_standard", _standard),
    ("microscope", _microscope),
    ("caliper", _caliper),
    ("printing", _printing),
    ("operators", _people),
    ("software", _software),
    ("open_decisions", _decisions),
)


def verify(evidence):
    """Return (results, summary).  Deterministic order."""
    results = []

    for group, fn in CHECK_GROUPS:
        def chk(level, code, passed, detail, _g=group):
            results.append({"group": _g, "code": code, "level": level,
                            "passed": bool(passed), "detail": detail})
        fn(evidence, chk)

    failed_mandatory = [r for r in results
                        if r["level"] == MANDATORY and not r["passed"]]
    failed_advisory = [r for r in results
                       if r["level"] == ADVISORY and not r["passed"]]
    summary = {
        "checks": len(results),
        "mandatory": sum(1 for r in results if r["level"] == MANDATORY),
        "advisory": sum(1 for r in results if r["level"] == ADVISORY),
        "mandatory_failed": len(failed_mandatory),
        "advisory_failed": len(failed_advisory),
        "failed_by_group": {g: sum(1 for r in failed_mandatory if r["group"] == g)
                            for g, _fn in CHECK_GROUPS},
        "verified": len(failed_mandatory) == 0,
    }
    return results, summary


def template():
    """A blank evidence file.  Every field is null: nothing is pre-assumed."""
    return {
        "_README": [
            "B2 reference-setup evidence.  Filling a field is a factual claim.",
            "Leave a field null until it is actually true; null, '', 'TBD' and",
            "'UNSPECIFIED' all read as NOT VERIFIED, which is the safe default.",
            "Verify with: python3 tools/verify_b2_setup.py --evidence <this file>",
            "This file records setup evidence only.  It is NOT a measurement",
            "record: reference values live in reference/reference_table.csv.",
        ],
        "recorded_by": None,
        "recorded_at": None,
        "scanner": {
            "instrument_id": None, "optical_dpi": None, "dpi_is_optical": None,
            "dpi_used_for_scan": None, "scan_mode": None, "bit_depth": None,
            "enhancement_off": None, "enhancement_items_disabled": [],
            "output_format": None, "resampling_or_rescaling": None,
            "single_session_all_panels": None, "scale_calibration_ref": None,
            "scale_factor_x": None, "scale_factor_y": None,
            "platen_nonuniformity_recorded": None, "frame_in_scan": None,
            "_note": "frame_in_scan must be false: S3 is frozen as NO",
        },
        "length_standard": {
            "standard_id": None, "type": None, "certificate_ref": None,
            "certificate_issued": None, "certificate_expires": None,
            "traceability": None, "stated_uncertainty_mm": None,
            "both_axes_verified": None,
            "_note": "transcribe the certificate; do not paraphrase it",
        },
        "microscope": {
            "instrument_id": None, "type": None,
            "has_xy_stage_with_readout": None, "stage_rotation_available": None,
            "reading_resolution_mm": None, "calibration_ref": None,
            "illumination_mode": None, "m1_procedure_read": None,
            "m1_checklist_available": None, "operator_trained_against_m1": None,
            "inter_operator_check_done": None, "repeats_planned": None,
            "raw_reading_format": None,
            "_note": "reading_resolution_mm is decision M2 and has no repository default",
        },
        "caliper": {
            "instrument_id": None, "resolution_mm": None,
            "calibration_record_ref": None, "used_for_glyph_reference": None,
            "_note": "used_for_glyph_reference must be false",
        },
        "printing": {
            "printer_id": None, "scale_verified_against_100mm_bar": None,
            "measured_check_bar_mm": None, "coupon_panels_printed": None,
            "stock_description": None, "stock_dimensionally_stable": None,
            "real_packaged_products_used_as_p0_sample": None,
        },
        "operators": {
            "scanner_operator": None, "microscope_operator": None,
            "microscope_blind_to_scanner_values": None,
        },
        "software": {
            "scan_measurement_tool": None,
            "scan_measurement_dry_run_passed": None,
            "png_conversion_verified_no_sharpening": None,
            "reference_validator_run_clean": None,
            "reference_table_committed_before_capture": None,
        },
        "open_decisions": dict(
            [(k, None) for k in OPEN_DECISION_KEYS] + sorted(SETTLED_DECISIONS.items())
        ),
    }


def load_evidence(path):
    if not os.path.exists(path):
        raise SetupEvidenceError("no such evidence file: %s" % path)
    try:
        data = load_json(path)
    except Exception as exc:                              # noqa: BLE001
        raise SetupEvidenceError("could not parse %s: %s" % (path, exc))
    if not isinstance(data, dict):
        raise SetupEvidenceError("%s must contain a JSON object" % path)
    return data


def report(results, summary, out=None):
    out = out or sys.stdout
    for group, _fn in CHECK_GROUPS:
        rows = [r for r in results if r["group"] == group]
        bad = [r for r in rows if not r["passed"]]
        out.write("%-16s %d checks, %d not satisfied\n"
                  % (group, len(rows), len(bad)))
        for r in bad:
            out.write("  [%s] %-42s %s\n" % (r["level"], r["code"], r["detail"]))
    out.write("-" * 78 + "\n")
    out.write("checks %d (mandatory %d, advisory %d); mandatory failed %d, "
              "advisory failed %d\n"
              % (summary["checks"], summary["mandatory"], summary["advisory"],
                 summary["mandatory_failed"], summary["advisory_failed"]))
    out.write("B2_SETUP_VERIFIED = %s\n" % ("YES" if summary["verified"] else "NO"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--evidence", help="setup evidence JSON to verify")
    ap.add_argument("--template", help="write a blank evidence file here")
    ap.add_argument("--json-out", help="write the machine-readable result here")
    a = ap.parse_args(argv)

    if a.template:
        dump_json(a.template, template())
        sys.stdout.write("blank evidence template written: %s\n" % a.template)
        sys.stdout.write("every field is null, so verification returns NO until "
                         "it is filled with real answers\n")
        return 0
    if not a.evidence:
        ap.error("one of --evidence or --template is required")

    try:
        ev = load_evidence(a.evidence)
    except SetupEvidenceError as exc:
        sys.stderr.write("B2_SETUP_VERIFIED = NO (%s)\n" % exc)
        return 2

    results, summary = verify(ev)
    report(results, summary)
    if a.json_out:
        dump_json(a.json_out, {"summary": summary, "checks": results,
                              "B2_SETUP_VERIFIED": "YES" if summary["verified"]
                              else "NO"})
    return 0 if summary["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
