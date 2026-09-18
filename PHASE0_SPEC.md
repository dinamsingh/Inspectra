# PHASE 0 ADVERSARIAL REVIEW — Part 3 of 3: Implementation specification

**Target:** desktop-first reference implementation (`Python 3.11 + OpenCV 4.x` pinned, NumPy, SciPy) jo Phase-0 question ka testable answer de. Android port Phase 0b hai, tab hi jab §Stop conditions pass ho.

**Non-goal:** UI, database, OCR, rules, reports. Phase 0 mein sirf measurement + uncertainty + abstention.

---

## 0. AS-BUILT RECONCILIATION (added by the consistency audit)

> **Status of this document:** §1–§9 are the *pre-implementation draft specification*.
> They are retained as the design record. Where they disagree with the shipped code,
> **the code and `phase0/config/*.json` are authoritative**, and the table below is the
> single normative reconciliation. No threshold was changed to produce this table; it
> only records what was actually built.

### 0.1 Module layout as built

| Draft (§1) | As built | Note |
|---|---|---|
| `types.py`, `imageio.py` | folded into `p0/core.py` | plus linear algebra, sRGB LUT, PNG codec, PRNG |
| `quality.py` | folded into `p0/measure.py` | quality metrics come out of the same profile scan |
| `frame_detect.py` | `p0/fiducial.py` | also contains the NDFID-1 dictionary and marker rendering bits |
| `glyph.py` | `p0/measure.py` | |
| `mc.py` (offline Monte Carlo) | **not implemented** | closed-form budget only; see `P0_ASSUMPTIONS.md` A-07 |
| `report.py` | `p0/results.py` + `p0/plots.py` | |
| — | `p0/camera.py`, `p0/render.py`, `p0/version.py` | camera model and synthetic renderer were not in the draft |
| `tools/make_synthetic.py` | `tools/experiments.py` + the renderer | fixtures are generated in-process, not written to disk first |
| `tools/run_batch.py` | `tools/run_experiment.py` (synthetic), `tools/run_real_batch.py` (physical) | |
| `tools/analyse_pilot.py` | `tools/analyse_results.py` | one analyser for both sources |
| `tools/calibrate_uncertainty.py` | **not implemented** | the model ships uncalibrated by design (A-07) |
| — | `tools/make_configs.py`, `make_frame_svg.py`, `make_coupons_svg.py`, `survey_frame.py`, `calibrate_camera.py` | |

### 0.2 Policy values as built

| Draft field (§2) | Draft value | As-built key | As-built value |
|---|---|---|---|
| `rho_px_per_mm_min` | 12.0 | `min_rho_px_per_mm` | **10.0** (hard floor; the *capture target* is >= 16 px/mm, see `P0_PROTOCOL.md` §4) |
| `stroke_px_min` | 4.0 | — | **not implemented as a gate** |
| `blur_sigma_mm_max` | 0.06 | `max_blur_sigma_mm` | 0.06 (unchanged) |
| `fiducial_edge_spread_px_max` | 1.5 | — | **not a gate.** Marker 10-90 edge rise is used to *compute* `blur_sigma_mm`; the separate `max_edge_rms_px = 0.60` gates the edge-line fit residual, a different quantity |
| `contrast_michelson_min` | 0.30 | `min_michelson_contrast` | 0.30 |
| `snr_min` | 20.0 | `min_snr` | 20.0 |
| `reproj_rms_px_max` / `reproj_max_px_max` | 0.25 / 0.60 | `max_reproj_rms_px` / `max_reproj_max_px` | 0.25 / 0.60 |
| `lomo_scale_rel_max` | 0.005 | `max_lomo_rel_spread` | 0.005 |
| `jacobian_ratio_max` | 3.0 | `max_jacobian_ratio` | 3.0 |
| `d_over_z_max` | 0.01 | `max_thickness_over_z` | 0.01 |
| `tilt_deg_max` | 5.0 | `max_view_tilt_deg` | **30.0 — and it is a different quantity.** 5 deg referred to *local print-plane tilt*, which is **not observable** from one view (A-06). The gate measures *view obliqueness*. The residual local tilt is carried as a bounded budget term, `residual_tilt_bound_deg = 3.0` in `uncertainty_model_v1.json` |
| `z_mm_range` | (170, 260) | `z_tolerance_frac` | 0.35 as a fraction of the profile's `z_calib_mm` |
| `burst_spread_mm_max` | 0.06 | `max_burst_sd_mm` | 0.06 |
| `interval_width_beta` | set after pilot | `max_interval_width_mm`, `max_interval_width_frac_of_threshold` | both `null` = gate deliberately **disabled** until the model is calibrated; reported as `evaluated: false` |
| `scanlines` | 32 | `scanlines` | **24** |
| `apex_fit_window_frac` | 0.30 | `apex_fit_window_frac` | **0.35** |
| bootstrap resamples | "e.g. 200" | `n_boot` in `measure.py` | **160** |
| — | — | `min_control_points` | 12 |
| — | — | `min_hull_margin_mm` | **8.0 flat** (the draft's `max(10 mm, 0.25 x ROI height)` rule was not implemented) |
| — | — | `max_clip_dark_frac`, `max_clip_bright_frac` | 0.005 each |
| — | — | `max_overshoot_ratio` | 0.08 |
| — | — | `min_scanline_fraction`, `max_median_crossings` | 0.50, 4 |
| — | — | `max_sensitivity_dev_frac`, `min_cluster_points`, `max_edge_fit_rms_mm` | 0.05, 4, 0.030 (the last one added in gate revision GP-v2) |

### 0.3 Uncertainty budget as built

The draft's `u_photometric_mm` and `u_device_mm` are **not separate fields**. The shipped
budget is:

```
u_random  = max(u_burst, mean(u_edge)/sqrt(n))      measured from the burst
u_common  = quadrature( u_scale, u_seg, u_thickness, u_ref, u_tilt,
                        u_extra, u_bias_correction )
u_c       = sqrt(u_random^2 + u_common^2)
```

`u_extra_mm` is the single slot reserved for the offline-calibrated photometric and
per-device residual; it is `0.0` today (`UM-v1-uncalibrated`). The draft's advice
"do not assume `k = 1.645`" is **not yet honoured** — 1.645 ships as a nominal value
and this is recorded as an open item in A-07.

### 0.4 Naming

Abstention statuses use the full prefix `PHYSICAL_SIZE_NOT_ESTABLISHED_<STAGE>`.
The draft's shorthand `PSNE_*` appears nowhere in the code. The eight stages match:
`PROFILE, FIDUCIAL, IMAGE_QUALITY, GEOMETRY, PLANARITY, SEGMENTATION, BURST,
UNCERTAINTY`.

### 0.5 Fixture and test identifiers

The draft's `FX-SYN-01..09` / `T-01..T-14` identifiers were not carried into the code.
Implemented as:

| Draft | As built |
|---|---|
| FX-SYN-01 ideal | `E_MATH-*` fixtures + `test_T01_ideal_accuracy` |
| FX-SYN-02/03 distortion, tilt | `E_DISTORT-offaxis` (2 variants), `E_TILT-*` |
| FX-SYN-04/05 blur, estimator | `E_BLUR-*`, `test_estimator_beats_max_minus_min_under_noise` |
| FX-SYN-06 gamma | `E_LINEARIZE-nominal` (`linear`, `gamma`, `gamma_glyph_only`) |
| FX-SYN-07 overshoot | `N_SHARPENING` |
| FX-SYN-08 offset/tilt injection | `N_PLANE_OFFSET_UNDECLARED-*`, `N_NONPLANAR_TILT-*`, `test_T08_*` |
| FX-SYN-09 marker faults | `N_WRONG_FIDUCIAL`, `N_MISSING_MARKER`, `test_T09_*` |
| T-11 gate invariant | `test_T11_gate_invariant_no_number_when_abstaining` |
| T-14 determinism | `test_T14_determinism` |
| T-13 golden regression | **not implemented** (`fixtures/golden/` does not exist); the committed `out/synthetic` set serves as the reference |
| FX-PHY-01..04, T-20..T-25 | specified in `P0_PROTOCOL.md`; **not yet executed** (A-12) |

### 0.6 Physical fixture geometry

| Draft | As built |
|---|---|
| frame outer 150 x 90 mm, window 100 x 30 mm, marker/checker band 20 mm | **outer 100 x 60 mm, window 50 x 20 mm, marker side 10 mm** (`tools/make_configs.py`) |
| coupon reference measurement "all 60 glyphs" | **20 panels x 5 heights x 4 shapes = 400 glyph instances** (`tools/make_coupons_svg.py`); the microscope cross-check subset is >= 15 |
| ChArUco border for control points | **NDFID-1** coded squares with edge-line corners (A-03) |

---

## 1. Repository layout

```
phase0/
  pyproject.toml            # pinned: opencv-python==<pin>, numpy, scipy, pydantic
  policy/
    measurand_policy_v1.json
    gate_policy_v1.json
    frames/FRAME-0001.json          # surveyed frame certificate
    cameras/DEV-A_main_4000x3000.json
  src/niyam_p0/
    __init__.py
    types.py                # dataclasses / pydantic models
    imageio.py              # load, luma, linearize, hash
    quality.py              # blur, clipping, contrast, overshoot
    frame_detect.py         # ChArUco/ArUco detection + frame identity
    geometry.py             # undistort, homography, LOMO, Z, tilt proxy
    glyph.py                # scanline subpixel edges + model fits
    uncertainty.py          # budget, combination, bounds
    gates.py                # gate evaluation + state machine
    pipeline.py             # orchestration -> MeasurementResult
    mc.py                   # OFFLINE Monte Carlo validator
    report.py               # JSON/JSONL writers, overlay renderer
  tools/
    calibrate_camera.py
    survey_frame.py
    make_synthetic.py       # FX-SYN fixtures
    run_batch.py
    analyse_pilot.py
  fixtures/
    synthetic/FX-SYN-01..09/
    golden/                 # frozen inputs + expected outputs
  out/                      # results, logs, overlays (gitignored)
  tests/
```

---

## 2. Core data structures

```python
# types.py  (all lengths in mm unless _px)

@dataclass(frozen=True)
class MeasurandPolicy:
    policy_id: str                  # "MP-v1"
    linearization: str              # "SRGB_EOTF"
    boundary_fraction: float        # 0.50
    sensitivity_fractions: tuple    # (0.40, 0.60)
    glyph_classes: dict             # {"FLAT_TOP": [...], "ROUND": [...], "NUMERAL": [...]}
    excluded: tuple                 # ("ACCENT","DOT","DESCENDER","PUNCT")
    aggregation: str                # "MIN_ELIGIBLE_GLYPH"
    scanlines: int                  # 32
    apex_fit_window_frac: float     # 0.30
    policy_hash: str

@dataclass(frozen=True)
class GatePolicy:
    policy_id: str                  # "GP-v1"
    rho_px_per_mm_min: float        # 12.0
    stroke_px_min: float            # 4.0
    blur_sigma_mm_max: float        # 0.06
    fiducial_edge_spread_px_max: float   # 1.5
    overshoot_ratio_max: float      # 0.08
    contrast_michelson_min: float   # 0.30
    snr_min: float                  # 20.0
    reproj_rms_px_max: float        # 0.25
    reproj_max_px_max: float        # 0.60
    lomo_scale_rel_max: float       # 0.005
    jacobian_ratio_max: float       # 3.0
    d_over_z_max: float             # 0.01
    tilt_deg_max: float             # 5.0
    z_mm_range: tuple               # (170.0, 260.0)
    burst_spread_mm_max: float      # 0.06
    interval_width_beta: float      # set AFTER pilot
    policy_hash: str

@dataclass(frozen=True)
class FrameCertificate:
    frame_id: str; serial: str
    dictionary: str                  # "DICT_5X5_100"
    expected_marker_ids: tuple
    control_points_mm: np.ndarray     # (N,2) surveyed
    control_point_u_mm: float         # survey uncertainty (1-sigma)
    thickness_mm: float; thickness_u_mm: float
    window_mm: tuple                  # (w,h) of measurement cut-out
    issued_at: str; expires_at: str
    certificate_hash: str

@dataclass(frozen=True)
class CameraProfile:
    profile_id: str; device_model: str
    physical_camera_id: str; resolution: tuple
    af_mode: str; ois_state: str      # "OFF" | "ON" | "UNKNOWN"
    K: np.ndarray; dist: np.ndarray
    K_cov: np.ndarray                 # bootstrap covariance
    reproj_holdout_rms_px: float
    z_calib_range_mm: tuple
    issued_at: str; expires_at: str
    profile_hash: str

@dataclass
class GlyphMeasurement:
    label: str; shape_class: str; index: int
    h_mm_50: float
    h_mm_40: float; h_mm_60: float    # sensitivity probes
    top_fit_rms_px: float; bottom_fit_rms_px: float
    scanlines_used: int
    u_edge_mm: float                  # per-glyph random
    eligible: bool

@dataclass
class UncertaintyBudget:
    u_burst_mm: float                 # live, common-mode
    u_scale_mm: float                 # live, common-mode
    u_geom_mm: float                  # live, common-mode (d/Z, tilt, Z band)
    u_photometric_mm: float           # offline-calibrated, common-mode
    u_device_mm: float                # offline-calibrated, common-mode
    u_common_mm: float                # quadrature of the above
    u_edge_mm: float                  # per-glyph random (for the deciding glyph)
    u_c_mm: float
    k_lower: float; k_upper: float    # one-sided coverage factors
    bias_correction_mm: float
    u_bias_correction_mm: float
    model_version: str

@dataclass
class MeasurementResult:
    run_id: str
    status: str                       # see state machine
    reason_codes: list[str]
    h_mm: float | None                # deciding (minimum eligible) glyph, bias-corrected
    lower_mm: float | None            # one-sided 95% lower bound
    upper_mm: float | None            # one-sided 95% upper bound
    threshold_mm: float | None
    decision: str | None              # MEETS / POTENTIAL_UNDERSIZE / BORDERLINE_REVIEW
    glyphs: list[GlyphMeasurement]
    budget: UncertaintyBudget | None
    gates: dict                       # gate_name -> {value, limit, passed}
    geometry: dict                    # rho, Z, tilt_proxy, reproj, lomo, H
    inputs: dict                      # image hashes, profile/frame/policy hashes, versions
    timings_ms: dict
```

---

## 3. Module interfaces and the exact OpenCV operations

### 3.1 `imageio.py`
```python
def load_burst(paths: list[Path]) -> BurstImages      # preserves raw bytes + sha256 each
def to_luma(bgr) -> np.ndarray                        # float32; cv2.cvtColor(..., COLOR_BGR2GRAY) on LINEARIZED channels
def linearize_srgb(img_u8) -> np.ndarray              # float32 0..1, sRGB EOTF (NOT a simple /255)
```
Rule: **linearize pehle, luma baad mein.** Gamma-space grayscale se 50% boundary biased hota hai (Part 1 F1.2).

### 3.2 `quality.py`
```python
def blur_sigma_px(luma, fiducial_edges) -> float      # from 10-90% edge spread of marker borders
def clipping(luma) -> dict                            # frac at 0 and at 1 inside ROI and inside paper region
def local_levels(luma, roi) -> (L_paper, L_ink, snr)  # robust percentiles + local noise sigma
def michelson(L_paper, L_ink) -> float
def overshoot_ratio(profiles) -> float                # ISP halo detector: pre/post-edge excursion
```

### 3.3 `frame_detect.py`
```python
def detect(luma_u8, cert: FrameCertificate) -> FrameDetection
```
OpenCV ops:
- `cv2.aruco.getPredefinedDictionary(cert.dictionary)`
- `cv2.aruco.CharucoBoard(...)` + `cv2.aruco.CharucoDetector(board, detector_params, refine_params)`
- `detector.detectBoard(img)` → `charucoCorners`, `charucoIds`, `markerCorners`, `markerIds`
- Fallback (pure-ArUco frame): `cv2.aruco.ArucoDetector(dict, params)`; `params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX`; `params.cornerRefinementWinSize = max(3, round(0.25*rho))`
Strictness:
- `set(markerIds) == set(cert.expected_marker_ids)`; no duplicates; no extras
- ≥12 control points (ChArUco: ≥24 recommended)
- each marker quad convex, aspect within tolerance, not clipped by image border

### 3.4 `geometry.py`
```python
def undistort_points(pts_px, prof) -> np.ndarray      # cv2.undistortPoints(..., P=prof.K)
def fit_homography(plane_mm, img_px_undist) -> HFit   # cv2.findHomography(method=0) + LM refine
def rho_px_per_mm(H, at_mm) -> float                  # from Jacobian singular values
def jacobian(H, p_mm) -> np.ndarray                   # analytic 2x2
def z_estimate_mm(rho, prof) -> float                 # Z ~= f_px / rho   (f_px = mean(K[0,0],K[1,1]))
def lomo_scale_spread(groups) -> float                # leave-one-group-out rel. scale spread
def tilt_proxy_deg(H, prof) -> float                  # decompose H with K -> plane normal angle
def map_to_plane(pts_px_undist, H) -> np.ndarray      # normalize(H^-1 p)
```
Normative stage order (freeze this, warna results silently change):
`raw luma → subpixel points (distorted space) → undistortPoints → H⁻¹ → mm → thickness correction`

Thickness correction:
```
h_corrected = h_raw_mm * (1.0 + cert.thickness_mm / Z_marker_mm)
```

### 3.5 `glyph.py` — the estimator (replaces contour/CC approach)
```python
def measure_glyph(luma_lin, roi, baseline_dir, policy) -> GlyphMeasurement
```
Algorithm:
1. Baseline direction: robust fit over ≥4 baseline-bearing glyph bases (`cv2.fitLine` with `DIST_HUBER`), or operator-supplied; record angle + uncertainty.
2. `n` = unit normal to baseline.
3. Generate `policy.scanlines` sample lines parallel to `n`, spanning the glyph's along-baseline width (skip outer 10% each side).
4. Per scanline: sample luma with `cv2.remap`-free direct bilinear sampling along the line; find **first and last** crossing of `L_50 = (L_paper+L_ink)/2` using linear interpolation between adjacent samples → subpixel top/bottom point.
5. Reject scanlines with: multiple crossings beyond 2 (stroke interaction), saturation, or |gradient| below noise floor.
6. **Top/bottom edge model:**
   - `FLAT_TOP`: robust line fit (Huber) to the top points; same for bottom; height = distance between lines at glyph centre.
   - `ROUND`: parabola fit over central `apex_fit_window_frac` of points; take vertex; same at bottom.
7. `u_edge` = combination of fit residual RMS and the fit's parameter standard error, converted to mm via local ρ.
8. Repeat whole step at 0.40 and 0.60 fractions → `h_40`, `h_60` (sensitivity band).

Notes: **koi `cv2.threshold`, `findContours`, `morphologyEx`, `connectedComponents` nahi.** Ye deliberate hai — Part 1 F7.1.

### 3.6 `uncertainty.py`
```python
def combine(live: LiveTerms, cal: CalibratedTerms, policy) -> UncertaintyBudget
def bounds(h, budget) -> (lower, upper)
```
Rules:
- Bounded systematic terms (thickness, sensitivity band, tilt bound) → `u = a/sqrt(3)` before quadrature.
- Bias is **corrected**, not added: `h_corr = h_raw - bias_correction`; only `u_bias_correction` enters the budget.
- Split common-mode vs per-glyph:
  `u_c(glyph) = sqrt(u_common^2 + u_edge(glyph)^2)`
- One-sided bounds: `lower = h_corr - k_lower * u_c`, `upper = h_corr + k_upper * u_c`, with `k` calibrated on the development set (do **not** assume 1.645).
- Deciding glyph = `argmin` over eligible glyphs of `h_corr`; if that glyph's `h_corr` is > 3 robust-sigma below the others → `reason_codes += ["MIN_GLYPH_OUTLIER"]` → review.

### 3.7 `gates.py` + state machine
```python
def evaluate(ctx) -> (status, reason_codes, gate_table)
```
```
NOT_REQUESTED
 → INPUT_LOADED
 → PROFILE_VALID            | PSNE_CALIBRATION        (missing/expired profile, camera-id mismatch, OIS unknown+unsupported)
 → FRAME_VALID              | PSNE_FIDUCIAL          (id-set mismatch, too few control points, wrong/expired frame)
 → IMAGE_QUALITY_VALID      | PSNE_IMAGE_QUALITY     (blur, clipping paper/ink, contrast, snr, overshoot)
 → GEOMETRY_VALID           | PSNE_GEOMETRY          (reproj, lomo, rho, jacobian, Z band, ROI-in-hull)
 → PLANARITY_ACCEPTED       | PSNE_NON_PLANAR        (tilt proxy, d/Z, frame-rock flag)
 → GLYPH_VALID              | PSNE_SEGMENTATION      (scanline rejects, fit rms, stroke px, multi-crossing)
 → BURST_CONSISTENT         | PSNE_BURST             (burst spread over limit)
 → UNCERTAINTY_ACCEPTABLE   | PSNE_UNCERTAINTY       (interval width over beta*u_validated)
 → DECISION: MEETS_SCREENING_THRESHOLD | POTENTIAL_UNDERSIZE | REQUIRES_OFFICER_REVIEW_BORDERLINE
```
Invariants (unit-tested):
- any `PSNE_*` ⇒ `h_mm/lower/upper/decision == None`
- gate table **always** fully populated (even for gates after the failing one → `evaluated: false`)
- new run never inherits a previous run's decision

### 3.8 `mc.py` (offline only)
Monte Carlo validator: resample control points, intrinsics (from `K_cov` bootstrap), surveyed coordinates, baseline; refit H; recompute heights. Output: MC-based `u` vs closed-form `u` comparison. Purpose: **verify** that the cheap closed-form model is not optimistic. Never runs on device.

---

## 4. Input / output contracts

**Input (one measurement run):**
```
run_dir/
  frames/0001.dng|jpg ... 0007.*      # burst, unmodified
  request.json
```
```json
{
  "run_id": "P0-2026-0417-0031",
  "frame_cert": "FRAME-0001",
  "camera_profile": "DEV-A_main_4000x3000",
  "measurand_policy": "MP-v1",
  "gate_policy": "GP-v1",
  "threshold_mm": "3.000",
  "glyph_selection": [
    {"label": "5", "shape_class": "NUMERAL_ROUND", "roi_px": [1820, 1440, 96, 120]}
  ],
  "operator_id": "OP-2",
  "declared_surface": "FLAT_PLATE_MOUNTED",
  "notes": "pilot panel P07, angle 12deg"
}
```

**Output:** `out/<run_id>/result.json` (canonical, sorted keys, decimal **strings**, no binary floats in persisted numbers), plus:
- `out/<run_id>/overlay.png` — source image with control points, ROI hull, scanlines, fitted top/bottom curves
- `out/<run_id>/profiles.csv` — per-scanline crossings (for audit/debug)
- `out/<run_id>/run.jsonl` — structured log

```json
{
  "run_id": "P0-2026-0417-0031",
  "status": "DECIDED",
  "decision": "POTENTIAL_UNDERSIZE",
  "reason_codes": [],
  "h_mm": "2.214", "lower_mm": "2.118", "upper_mm": "2.310",
  "threshold_mm": "3.000",
  "glyphs": [{"label":"5","h_mm_50":"2.214","h_mm_40":"2.252","h_mm_60":"2.181","u_edge_mm":"0.019","eligible":true}],
  "budget": {"u_burst_mm":"0.021","u_scale_mm":"0.006","u_geom_mm":"0.009",
             "u_photometric_mm":"0.041","u_device_mm":"0.023","u_common_mm":"0.053",
             "u_c_mm":"0.056","k_lower":"1.71","k_upper":"1.71",
             "bias_correction_mm":"-0.037","u_bias_correction_mm":"0.015","model_version":"UM-v1"},
  "geometry": {"rho_px_per_mm":"15.82","z_mm":"196.4","tilt_proxy_deg":"2.9",
               "reproj_rms_px":"0.118","reproj_max_px":"0.284","lomo_scale_rel":"0.0016"},
  "gates": {"blur_sigma_mm":{"value":"0.031","limit":"0.060","passed":true}},
  "inputs": {"burst_sha256":["..."],"frame_cert_hash":"...","camera_profile_hash":"...",
             "measurand_policy_hash":"...","gate_policy_hash":"...",
             "opencv_version":"4.x.y","algorithm_version":"P0-1.0.0","platform":"linux-x86_64"}
}
```

---

## 5. Logging and reproducibility

**Logging (JSONL, one object per stage):** stage name, duration_ms, key inputs/outputs, gate values, and any rejection. Log par **koi image bytes nahi**, sirf hashes.

**Reproducibility rules:**
1. Pin `opencv-python`, `numpy`, `scipy` exact versions; record in every result.
2. Record `algorithm_version`, all four policy/cert hashes, and `platform`.
3. Any RNG: own PRNG (`numpy.random.Generator(PCG64(seed))`), `seed = sha256(run_id | algorithm_version | policy_hash)`; **but** claim only: *same platform + same pinned deps ⇒ bit-identical; cross-platform ⇒ `|Δh| ≤ 0.005 mm`*.
4. Golden regression: `fixtures/golden/` mein frozen inputs + expected outputs; CI compares within tolerance.
5. Results are append-only files; re-run writes a new `run_id`.

---

## 6. Acceptance tests (must all pass before Phase 0b / Android port)

### 6.1 Unit / synthetic (fast, deterministic)
| ID | Test | Pass criterion (hypothesis) |
|---|---|---|
| T-01 | FX-SYN-01 ideal render, 12 known heights | abs error ≤0.005 mm each |
| T-02 | FX-SYN-02 known distortion, undistortion ON | ≤0.010 mm |
| T-03 | FX-SYN-02 with undistortion OFF | Δ reported (this is experiment E3, not a pass/fail) |
| T-04 | FX-SYN-03 tilt 0–40° | ≤0.020 mm where blur gate passes |
| T-05 | FX-SYN-04 blur sweep | monotone `u` growth; bias drift ≤0.02 mm up to σ=0.06 mm |
| T-06 | FX-SYN-05 estimator comparison | model-fit bias < 1/3 of `max−min` bias at matched noise |
| T-07 | FX-SYN-06 gamma vs linear | linearized path bias closer to truth; shift documented |
| T-08 | FX-SYN-07 injected overshoot | detector flags ≥90%, FP ≤5% |
| T-09 | FX-SYN-08 injected d and α | measured error matches `d/Z` and `cos α` prediction within 10% |
| T-10 | FX-SYN-09 marker faults | 100% hard-fail with correct reason code |
| T-11 | Gate invariants | no numeric result ever emitted with a `PSNE_*` status |
| T-12 | Stale-result test | new failing run never shows previous decision |
| T-13 | Golden regression | within tolerance |
| T-14 | Determinism | same platform re-run bit-identical |

### 6.2 Physical (pilot)
| ID | Test | Pass criterion |
|---|---|---|
| T-20 | Frame survey repeatability (10 measurements) | SD ≤0.03 mm; documented |
| T-21 | Reference cross-method (scanner vs microscope, ≥15 glyphs) | mean abs diff ≤0.03 mm |
| T-22 | Control coupon stability over 5 days | within control limits |
| T-23 | Pilot bias/repeatability/device effect | §16 go/no-go table |
| T-24 | Stress block abstention | unsafe acceptance ≤2% |
| T-25 | Interval plausibility (pilot, indicative only) | observed coverage 85–100% (final coverage claim needs sealed set) |

---

## 7. Stop conditions (binary, preregistered)

**HARD STOP — do not build Android measurement UI, do not put mm claims in PPT:**
1. T-01 fails (pipeline math itself wrong) → fix code, re-run; no field work.
2. Reference cross-method disagreement >0.06 mm → no accuracy claim possible.
3. Residual SD after global bias correction >0.15 mm at the 3 mm class → measurement claim downgrade.
4. Unsafe-condition acceptance >5% → abstention unsafe; USP invalid as stated.
5. Nominal-condition gate acceptance <50% → fixture/protocol redesign before any demo promise.

**CONDITIONAL PROCEED (narrow the claim, don't widen the gates):**
- Device effect >0.12 mm → claim becomes "per-device-calibrated, on tested devices".
- Only one font class stable → claim restricted to that class.
- Only JPEG works (no RAW) → claim restricted to that capture mode, bias documented.
- Interval must be widened to achieve coverage → widen it and accept higher abstention/borderline rate.

**Never allowed:** pilot ke baad gates loosen karke pass dikhana; sealed-set reset ke bina policy change; abstained cases ko accuracy denominator se chupana.

---

## 8. Smallest working Phase-0 prototype (**P0-min**)

> Question to answer: *"Kya NiyamDrishti controlled planar conditions mein printed glyph extent ko millimetres mein reliably estimate kar sakta hai, uski uncertainty quantify kar sakta hai, aur unsafe conditions par abstain kar sakta hai?"*

### P0-min scope — exactly this, nothing more

**Hardware/artifacts (1–2 days):**
1. **One** ChArUco-border frame: outer ~150×90 mm, window ~100×30 mm, matte film/acrylic, serial `FRAME-0001`, thickness measured with caliper.
2. Frame surveyed with calibrated caliper (10 repeats) → `FRAME-0001.json`.
3. **One** rigid flat backing plate; coupons glued flat.
4. **20 printed coupons**: 4 fonts × 5 nominal heights (~1.2/2.0/3.0/4.0/6.0 mm), 3 eligible glyphs each.
5. Reference measurement of all 60 glyphs on a **calibrated flatbed scanner @2400 dpi** using the *same* algorithm; 15 glyphs cross-checked on a measuring microscope.

**Software (4–6 days, desktop only):**
6. `make_synthetic.py` + FX-SYN-01…09 and tests T-01…T-14.
7. `frame_detect` + `geometry` + `glyph` (scanline estimator) + `gates` + closed-form `uncertainty`.
8. `run_batch.py` → `result.json` + overlay per run.
9. `analyse_pilot.py` → bias/repeatability/device/gate tables + selective-risk curve.
10. `calibrate_camera.py` for 2 devices (and the E3 with/without-undistortion comparison).

**Capture (1–2 days):**
11. Phone used **only as a camera**: manual/pro mode, AF locked at the working distance, OIS off if possible, HDR/night/beauty off, highest-quality JPEG (+DNG where available), **burst of 7**, tripod/stand for repeats, handheld for the operator-variability block.
12. 240 nominal captures + ~60 stress captures, as per Part 1 §16.

**Analysis and decision (1 day):**
13. Produce `PHASE0_RESULT.md` containing: bias, repeatability, device effect, gate acceptance, unsafe acceptance, abstention rate, ablations (E1 estimator, E2 linearization, E3 undistortion, E4 RAW/JPEG), and the **go / conditional / no-go** verdict against §7.

### Explicitly OUT of P0-min
Android app, UI, Room/SQLCipher, OCR, rules engine, reports, sync, multi-glyph auto-detection, contours/morphology/CC, on-device Monte Carlo, curved surfaces, 450-panel sealed set, any PPT number.

### P0-min deliverables
| Artifact | Meaning |
|---|---|
| `FRAME-0001.json` + survey record | reference chain exists |
| 2 × `CameraProfile` + E3 result | calibration necessity answered |
| Synthetic test report (T-01…T-14) | the maths is correct, independent of physics |
| Reference table (60 glyphs, 2 methods) | ground truth exists and is consistent |
| 300 `result.json` + overlays | reproducible measurement evidence |
| `PHASE0_RESULT.md` | the one honest answer to the Phase-0 question |

### The single sentence P0-min must be able to fill in

> "On 20 controlled planar coupons, **N** glyphs, **2** phones, **2** operators, our Phase-0 pipeline estimated printed-ink glyph extent with bias **[x] mm**, repeatability SD **[y] mm**, P95 absolute error **[z] mm**, while abstaining on **[a]%** of nominal captures and accepting **[b]%** of deliberately unsafe captures."

Jab tak ye sentence real numbers se bhar nahi sakta, Android measurement feature, hero demo aur USP claim — teeno **blocked** hain.

---

## 9. Amendments required in SOLUTION_LOCK_V2.md (delta list, not applied yet)

| V2 location | Current | Required change |
|---|---|---|
| §10.1 | `h = max − min` over contour | model-fit estimator (line/parabola apex) |
| §10.1 | 50% boundary, space unspecified | linearized luminance + `linearization_version` |
| §10.2 step 7 | contour + topology stability | scanline crossings; drop topology gate for Phase 0 |
| §10.3 | "≥25 source px across minimum height" | ρ ≥12 px/mm, stroke ≥4 px, blur σ ≤0.06 mm |
| §10.3 | plane offset/flatness ≤0.10 mm each | thickness correction `(1+d/Z)`, `d/Z ≤1%`, local tilt ≤5° |
| §10.3 | contrast "50 levels 8-bit" | Michelson ≥0.30 (linear) + SNR floor |
| §10.3 | interval width `max(0.10, 0.15T)` | `β × u_validated`, β frozen after pilot |
| §10.3 | — | add: paper clipping, overshoot ratio, burst spread, camera-ID match, Z band |
| §11.1 | CMM/optical comparator survey | caliper/scanner survey sufficient; CMM optional |
| §11.1 | frame geometry unspecified | 150×90 mm outer, 100×30 mm window, ChArUco border, matte film/acrylic |
| §11.2 | — | add: physical camera-ID pinning, OIS off, focus-breathing band, bootstrap covariance |
| §12.2 | 1000-sample MC on device | closed-form calibrated model + 7-frame burst; MC offline |
| §12.1/12.2 | `u_model` in quadrature | correct bias; combine only correction uncertainty; `a/√3` for bounded terms |
| §12.2 | SHA-256 seed ⇒ deterministic replay | same-platform bit-identical; else ±0.005 mm tolerance |
| §12 | — | add common-mode vs per-glyph decomposition; min-glyph outlier → review |
| §13.1 | state machine | add BURST_CONSISTENT, paper-clipping, camera-ID, Z-band states |
| §23A | 450 panels, 3 recaptures, microscope GT, angles 0/20/35° | ~120 preregistered panels; scanner GT primary + cross-check; 35° = stress class |
| §23A | — | add synthetic ground-truth harness as a first-class fixture |
| Phase 0 build order | Android app spike | desktop-first P0-min; Android = Phase 0b |
| §27 G1 | "≤0.10 mm plane/flatness control" | replace with corrected-thickness + tilt criteria |
| §27 G2/G3 | targets | keep, but add T-01…T-14 synthetic gate as a precondition |

**Recommendation:** ye amendments V2 mein apply karne se pehle approve karao, kyunki V2 "FROZEN" baseline hai; main silently frozen document edit nahi kar raha.
