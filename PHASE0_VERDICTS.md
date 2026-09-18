# PHASE 0 ADVERSARIAL REVIEW — Part 2 of 3: Decision verdicts

Legend: **A = PASS** (keep as-is) · **B = NEEDS MODIFICATION** · **C = REMOVE** (from Phase 0) · **D = UNKNOWN / NEEDS EXPERIMENT**

## A. Measurand and estimator

| # | Phase-0 decision (V2) | Verdict | Action |
|---|---|:--:|---|
| 1 | Measure physical glyph extent in mm, not font size / OCR box | **A** | keep; strongest part of V2 |
| 2 | Measure perpendicular to fitted baseline | **A** | keep; log baseline angle + its uncertainty |
| 3 | `h = max(n·p) − min(n·p)` over contour points | **B** | replace with scanline + fitted top/bottom model (line for flat-top, parabola apex for round) |
| 4 | 50% ink/paper transition boundary | **B** | keep 50%, but define on **linearized** luminance; freeze `linearization_version` |
| 5 | 40/50/60% sensitivity contours as systematic band | **B** | keep as sensitivity probe; convert bound to `a/√3` before combining |
| 6 | Contrast gate "≥50 levels, 8-bit" | **B** | redefine as linear-space Weber/Michelson + SNR floor |
| 7 | "Eligible glyphs" left undefined | **B** | explicit whitelist + shape class (FLAT_TOP / ROUND / NUMERAL); exclude accents, dots, descenders in Phase 0 |
| 8 | Report `h_ink_50` as the claim, not statutory character height | **A** | keep; add separate `h_nominal_unknown = true` field |
| 9 | Aggregate by **minimum eligible glyph**, not median | **B** | keep rule, but split common-mode scale vs per-glyph noise; flag min-outlier to review |
| 10 | Topology stability across 40/50/60% as a hard gate | **C** | remove from Phase 0 (scanline estimator has no topology); replace with edge-profile shape checks |

## B. Physical reference frame

| # | Decision | Verdict | Action |
|---|---|:--:|---|
| 11 | Co-planar fiducial enclosing the ROI (no adjacent ruler) | **A** | keep; this is the correct core idea |
| 12 | Four corner markers, ROI inside convex hull, margin rule | **A** | keep |
| 13 | ArUco square corners as geometric control points | **B** | switch to ChArUco border (markers for ID, chessboard corners for geometry) |
| 14 | CMM / optical-comparator survey mandatory | **B** | downgrade to optional; calibrated caliper/scanner survey sufficient (contribution ≈0.0005 mm) |
| 15 | `≤0.10 mm` absolute marker/text plane offset gate | **C** | remove — impossible with a physical frame; replace with measured thickness `d` + correction `(1 + d/Z)` and gate `d/Z ≤ 1%` |
| 16 | `≤0.10 mm` absolute local flatness gate | **B** | replace with **local tilt ≤5°** + bow effect `δ/Z` + LOMO scale consistency |
| 17 | Frame material/geometry unspecified | **B** | specify: rigid film/acrylic/aluminium, matte; outer ≈150×90 mm, window ≈100×30 mm |
| 18 | Serialized frame identity | **A** | keep; bind marker-ID set + serial + expiry; hard-fail mismatch |

## C. Camera, capture, platform

| # | Decision | Verdict | Action |
|---|---|:--:|---|
| 19 | Per-device/resolution/focus intrinsic calibration | **D** | run E3: measure Δh with vs without undistortion; possibly defer if P95 Δh < 0.02 mm |
| 20 | ChArUco calibration, ≥20 views, Brown–Conrady | **A** | keep; add bootstrap covariance (OpenCV gives only std-devs) |
| 21 | Lock + hash capture settings | **A** | keep; extend to **physical camera ID** (macro/ultrawide switch trap) |
| 22 | OIS/EIS handling | **C→B** | absent in V2 → **add**: force off if supported; else mark device and absorb in burst term |
| 23 | Working distance / DOF / tilt trade-off | **B** | absent in V2 → add: Z ∈ 180–240 mm, ρ ≥ 12 px/mm, nominal tilt ≤25° |
| 24 | RAW vs JPEG capture | **D** | run E4 on both; RAW availability is device-dependent |
| 25 | Single-frame capture | **B** | change to **burst of 7 frames** per measurement (gives live `u_burst`) |
| 26 | Same-day control coupon | **A** | keep; cheapest real safeguard |

## D. Geometry pipeline

| # | Decision | Verdict | Action |
|---|---|:--:|---|
| 27 | Undistort **points**, not the image | **A** | keep; make stage order normative |
| 28 | Normalized DLT + nonlinear refinement | **A** | keep; pin OpenCV version |
| 29 | Map source-image subpixel points via `H⁻¹`; never measure a resampled bitmap | **A** | keep; this is a genuinely good decision |
| 30 | Reprojection RMS ≤0.25 px / max ≤0.60 px | **B** | keep as *fit* gate; explicitly stop treating it as planarity evidence |
| 31 | Leave-one-marker-out scale ≤0.5% | **A** | keep; strengthen with ChArUco sub-region groups (6–8) |
| 32 | "≥25 source px across minimum height" | **B** | restate physically: ρ ≥ 12 px/mm, stroke ≥4 px, blur σ ≤0.06 mm |
| 33 | Jacobian singular-value ratio ≤3 | **A** | keep |

## E. Uncertainty and decision

| # | Decision | Verdict | Action |
|---|---|:--:|---|
| 34 | Quantified uncertainty attached to every estimate | **A** | keep; this is the USP |
| 35 | 1000-sample **on-device** Monte Carlo per capture | **C** | remove from device; keep MC as offline analysis tool |
| 36 | Empirically calibrated uncertainty model | **B** | promote to primary: `u_burst ⊕ u_scale ⊕ u_geom ⊕ u_photometric ⊕ u_device` |
| 37 | Bias term `u_model` inside quadrature | **B** | correct the bias; combine only the correction's uncertainty |
| 38 | Coverage factor `k` from data; no blind `k=2` | **A** | keep; freeze on development set, evaluate on sealed set |
| 39 | Bit-deterministic MC replay via SHA-256 seed | **B** | limit claim to same binary/ABI; store outputs; define replay tolerance |
| 40 | Guard band `L ≥ T` / `U < T` / else review | **A** | keep logic; define L and U as explicit one-sided bounds |
| 41 | Width gate `U−L ≤ max(0.10 mm, 0.15T)` | **B** | replace with validated-uncertainty-derived gate; current form is internally inconsistent |
| 42 | No rounding before comparison | **A** | keep |

## F. Abstention

| # | Decision | Verdict | Action |
|---|---|:--:|---|
| 43 | Monotonic gate state machine with reason codes | **A** | keep |
| 44 | Stale result invalidation on new capture | **A** | keep; test explicitly |
| 45 | Ink-side saturation gate only | **B** | add paper-side clipping gate |
| 46 | Fiducial edge-spread ≤1.5 px | **A** | keep; add overshoot/halo detector |
| 47 | Burst-consistency gate | **B** | absent → add |
| 48 | Policy versioning of gate thresholds | **B** | absent → add `policy_hash` in every result; loosening ⇒ sealed-set reset |
| 49 | Report abstention rate with accuracy | **A** | keep; selective-risk curve mandatory |

## G. Validation

| # | Decision | Verdict | Action |
|---|---|:--:|---|
| 50 | Microscope-only ground truth | **B** | add calibrated-scanner protocol as primary practical route + cross-method check |
| 51 | Nominal artwork height as ground truth | **C** | never; printer scaling unknown |
| 52 | 450-panel sealed set, 3 recaptures, + stress | **B** | infeasible in SIH timeline; reduce to preregistered ~120 panels, keep roadmap |
| 53 | Validation angles 0/20/35° as accuracy strata | **B** | 35° becomes stress/abstention class (DOF-limited at close range) |
| 54 | Panel-level statistical unit, cluster analysis | **A** | keep; good statistics |
| 55 | Synthetic ground-truth harness | **B** | absent in V2 → **add as first fixture** (only way to verify the math exactly) |
| 56 | 20-panel pilot to "expose model error" | **B** | define purpose/design/criteria explicitly (see Part 1 §16) |

## H. Sequencing

| # | Decision | Verdict | Action |
|---|---|:--:|---|
| 57 | Phase 0 as Android implementation | **B** | desktop-first Python/OpenCV; phone = camera only |
| 58 | Stop condition: "downgrade if interval not useful" | **B** | make numeric and preregistered (Part 1 §16 table) |
| 59 | Measurement feature gated behind G1–G4 | **A** | keep; strongest process safeguard in V2 |

### Verdict tally (59 decisions)

- **A (PASS):** 24
- **B (NEEDS MODIFICATION):** 28
- **C (REMOVE from Phase 0):** 4 — topology-stability gate (#10), absolute plane-offset gate (#15), on-device Monte Carlo (#35), nominal-artwork-height as ground truth (#51)
- **C→B (missing item that must be added):** 1 — OIS/EIS handling (#22)
- **D (NEEDS EXPERIMENT):** 2 — intrinsic-calibration necessity (#19), RAW-vs-JPEG effect (#24)

**Interpretation:** V2 ka Phase-0 *philosophy* (co-planar reference, no resampling, uncertainty, abstention, gating) largely correct hai — isliye 24 straight passes. Failures overwhelmingly **estimator, photometric definition, platform reality aur mis-scaled tolerances** mein hain, architecture mein nahi. Ye good news hai: Phase 0 salvageable hai without redesigning the product.
