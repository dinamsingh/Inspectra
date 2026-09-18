# P0-min result schema

Two artefacts per experiment set:

* `out/<set>/runs/<run_id>/result.json` -- full machine-readable record
* `out/<set>/results.csv` -- one flat row per run, for analysis

plus `manifest.json` (configuration + fixture hashes), `run.log`, and
`analysis/analysis.json`, `analysis/RESULT.md`, `analysis/plots/*.svg`.

## result.json

```
schema_version            "p0-result-1"
run_id                    stable id; "<fixture>__<variant>" for synthetic runs
status                    MEASURED | PHYSICAL_SIZE_NOT_ESTABLISHED_<STAGE>
reason_codes              [ ... ] machine readable abstention reasons
measurement
  h_mm                    bias-corrected estimate, or null when abstaining
  lower_mm / upper_mm     one-sided bounds (k_lower / k_upper), or null
  threshold_mm            configured engineering threshold (NOT a legal limit)
  decision                MEETS_SCREENING_THRESHOLD | POTENTIAL_UNDERSIZE |
                          REQUIRES_OFFICER_REVIEW_BORDERLINE | null
display                   the same headline numbers as decimal strings
budget
  n_frames, h_raw_mean_mm, burst_sd_mm
  u_burst_mm, u_edge_floor_mm, u_random_mm
  u_scale_mm, u_seg_mm, u_thickness_mm, u_ref_mm, u_tilt_mm
  u_extra_mm, u_bias_correction_mm, u_common_mm, u_c_mm
  bias_correction_mm, h_corrected_mm
  k_lower, k_upper, lower_mm, upper_mm, interval_width_mm
  model_version, model_calibrated
metrics                   the aggregated values the gates consumed
gates
  rows[]                  {stage, gate, value, limit, mode, passed, evaluated}
  failed_stage, failed_gate
per_frame[]               per-frame geometry, quality and height values
frame_errors[]            per-frame detection/segmentation failures
inputs                    algorithm_version, policy hashes, frame cert hash,
                          camera profile id, frames requested/ok
context                   profile id, calibration distance, declared flatness,
                          operator/panel metadata for physical runs
ground_truth              synthetic: exact true_ink_height_mm and the full scene
                          spec; physical: the reference measurement and method
timing_s
```

### Invariants (enforced by `tests/test_p0.py`)
1. `status != MEASURED` implies `h_mm`, `lower_mm`, `upper_mm` and `decision` are
   all `null`.
2. `gates.rows` always contains every gate; gates after the first failure have
   `evaluated: false`.
3. A `null` limit means the gate is deliberately disabled and is reported as
   `evaluated: false` (used for the interval-width gate until the uncertainty
   model is calibrated).
4. A `NaN` metric fails its gate closed.

## results.csv columns

Identity: `run_id, fixture_id, experiment, variant, source, safety_class`

Outcome: `status, decision, reason_codes, failed_stage, failed_gate,
frames_ok, frames_requested`

Measurement: `true_h_mm, h_mm, lower_mm, upper_mm, threshold_mm, error_mm,
abs_error_mm, covered, h_raw_mean_mm`

Estimator ablation: `h_maxminus_min_mm, maxminus_min_error_mm`

Uncertainty: `burst_sd_mm, u_random_mm, u_scale_mm, u_seg_mm, u_c_mm,
interval_width_mm`

Conditions: `rho_min_px_per_mm, blur_sigma_mm, michelson_contrast, snr,
overshoot_ratio, reproj_rms_px, reproj_max_px, edge_rms_px, lomo_rel_spread,
view_tilt_deg, z_mm, hull_margin_mm, jacobian_ratio, scanline_fraction,
median_crossings, thickness_over_z, clip_bright_frac, clip_dark_frac`

Scene / provenance: `glyph_shape, shape_class, design_h_mm, ink_spread_mm,
pose_tilt_deg, pose_z_mm, glyph_plane_offset_mm, glyph_plane_tilt_deg,
undistort_enabled, linearize_enabled, algorithm_version, timing_s`

Physical runs additionally: `panel_id, operator, device, repeat, angle_deg,
reference_method, glyph_label`

Notes:
* `true_h_mm` is the exact rendered ink extent for synthetic runs and the
  reference-instrument measurement for physical runs.
* `covered` is 1 when `lower_mm <= true_h_mm <= upper_mm`.
* Empty cells mean "not applicable" or "not computed because the run abstained" --
  they are never zero-filled.
* All floats are written with 6 decimals; `NaN` and infinities become empty.

## Determinism

`inputs.algorithm_version` plus the three policy hashes and the frame-certificate
hash identify everything that can change a number.  For the same interpreter and
platform, re-running a fixture reproduces identical values
(`test_T14_determinism`); across platforms compare with a tolerance
(see A-15), not byte equality.
