# P0-min synthetic experiment result

**Overall verdict: PASS**

All criteria are pre-registered in `docs/P0_CRITERIA.md`.  Numbers below
are measured on the synthetic harness, where ground truth is exact; they
are NOT physical-camera results and are NOT a legal accuracy claim.

## Verdict

| Criterion | Result | Detail |
|---|---|---|
| C11_safe_measure_rate | PASS | measure rate on SAFE=1.00 (>=0.80) |
| C1_arithmetic | PASS | max|err|=0.00797 mm <= 0.010 |
| C2_accuracy | PASS | bias=+0.0005 (<=0.030), p95|err|=0.0054 (<=0.060) |
| C3_repeatability | PASS | median burst SD=0.0025 mm (<=0.030) |
| C4_coverage | PASS | coverage=1.000 on n=17 (>=0.90); k is NOMINAL, not validated |
| C5_estimator | PASS | model-fit MAE=0.0018 vs max-minus-min MAE=0.0027 |
| C6_linearisation | PASS | linear err=0.0004 vs gamma-glyph err=-0.0441; full gamma: PHYSICAL_SIZE_NOT_ESTABLISHED_GEOMETRY |
| C7_unsafe_detection | PASS | abstained 11/11 |
| C8_decision_safety | PASS | false-clear=0 of 4 undersize; false-accuse=0 of 4 compliant |
| C9_undetectable_documented | PASS | single-view undetectable defects measured with |err| up to 0.1847 mm; these require fixture control, not gates |

## Accuracy on nominal (SAFE) conditions

| quantity | value |
|---|---|
| n_runs | 17.00000 |
| n_measured | 17.00000 |
| measure_rate | 1.00000 |
| bias_mm | 0.00052 |
| mae_mm | 0.00175 |
| p95_abs_error_mm | 0.00544 |
| max_abs_error_mm | 0.00802 |
| median_burst_sd_mm | 0.00246 |
| coverage | 1.00000 |
| coverage_n | 17.00000 |
| median_interval_width_mm | 0.05237 |

## Abstention on defects the gates target

| fixture | status | stage | gate |
|---|---|---|---|
| N_EXCESS_PERSPECTIVE | PHYSICAL_SIZE_NOT_ESTABLISHED_FIDUCIAL | FIDUCIAL | FIDUCIAL_MISSING_MARKER |
| N_GLARE_SATURATION | PHYSICAL_SIZE_NOT_ESTABLISHED_IMAGE_QUALITY | IMAGE_QUALITY | michelson_contrast |
| N_LOW_CONTRAST | PHYSICAL_SIZE_NOT_ESTABLISHED_IMAGE_QUALITY | IMAGE_QUALITY | michelson_contrast |
| N_MISSING_MARKER | PHYSICAL_SIZE_NOT_ESTABLISHED_FIDUCIAL | FIDUCIAL | FIDUCIAL_MISSING_MARKER |
| N_MOTION_BLUR | PHYSICAL_SIZE_NOT_ESTABLISHED_IMAGE_QUALITY | IMAGE_QUALITY | blur_sigma_mm |
| N_SHARPENING | PHYSICAL_SIZE_NOT_ESTABLISHED_IMAGE_QUALITY | IMAGE_QUALITY | clip_dark_frac |
| N_TINY_TEXT | PHYSICAL_SIZE_NOT_ESTABLISHED_IMAGE_QUALITY | IMAGE_QUALITY | blur_sigma_mm |
| N_UNSTABLE_BOUNDARY-0.15 | PHYSICAL_SIZE_NOT_ESTABLISHED_SEGMENTATION | SEGMENTATION | median_crossings |
| N_UNSTABLE_BOUNDARY-0.30 | PHYSICAL_SIZE_NOT_ESTABLISHED_SEGMENTATION | SEGMENTATION | median_crossings |
| N_UNSTABLE_BOUNDARY-0.50 | PHYSICAL_SIZE_NOT_ESTABLISHED_SEGMENTATION | SEGMENTATION | median_crossings |
| N_WRONG_FIDUCIAL | PHYSICAL_SIZE_NOT_ESTABLISHED_FIDUCIAL | FIDUCIAL | FIDUCIAL_MISSING_MARKER |

## Defects a single view cannot detect

| fixture | status | error (mm) | u_c (mm) | covered | reproj RMS px | LOMO |
|---|---|---|---|---|---|---|
| N_NONPLANAR_TILT-10 | MEASURED | -0.0456 | 0.0159 | 0.0 | 0.121 | 0.00023 |
| N_NONPLANAR_TILT-20 | MEASURED | -0.1847 | 0.0162 | 0.0 | 0.092 | 0.00020 |
| N_PLANE_OFFSET_UNDECLARED-1.5 | MEASURED | 0.0224 | 0.0153 | 1.0 | 0.099 | 0.00023 |
| N_PLANE_OFFSET_UNDECLARED-5.0 | MEASURED | 0.0802 | 0.0148 | 0.0 | 0.094 | 0.00022 |

## Guard-band decisions

| fixture | true (mm) | threshold | truly undersize | decision | interval |
|---|---|---|---|---|---|
| E_DECISION-2.40 | 2.400 | 3.000 | True | POTENTIAL_UNDERSIZE | [2.3740, 2.4274] |
| E_DECISION-2.70 | 2.700 | 3.000 | True | POTENTIAL_UNDERSIZE | [2.6762, 2.7279] |
| E_DECISION-2.85 | 2.850 | 3.000 | True | POTENTIAL_UNDERSIZE | [2.8258, 2.8773] |
| E_DECISION-2.95 | 2.950 | 3.000 | True | POTENTIAL_UNDERSIZE | [2.9251, 2.9758] |
| E_DECISION-3.05 | 3.050 | 3.000 | False | MEETS_SCREENING_THRESHOLD | [3.0230, 3.0720] |
| E_DECISION-3.15 | 3.150 | 3.000 | False | MEETS_SCREENING_THRESHOLD | [3.1262, 3.1791] |
| E_DECISION-3.30 | 3.300 | 3.000 | False | MEETS_SCREENING_THRESHOLD | [3.2743, 3.3262] |
| E_DECISION-3.60 | 3.600 | 3.000 | False | MEETS_SCREENING_THRESHOLD | [3.5735, 3.6261] |

## Ablations

| ablation | outcome |
|---|---|
| linearisation (linear) | err=0.0004 |
| linearisation (gamma, end to end) | PHYSICAL_SIZE_NOT_ESTABLISHED_GEOMETRY (gate reproj_rms_px) |
| linearisation (gamma, glyph only) | err=-0.0441 |
| undistortion on | err=0.0011 reproj=0.080 px |
| undistortion off | err=n/a reproj=0.822 px |
| estimator: fitted extreme | MAE=0.0018 |
| estimator: max-minus-min | MAE=0.0027 |

