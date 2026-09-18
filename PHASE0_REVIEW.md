# SIH26034 — NiyamDrishti
# PHASE 0 ADVERSARIAL REVIEW — Part 1 of 3: Technical findings

**Reviewer role:** senior adversarial technical reviewer + implementation architect.
**Baseline under review:** `SOLUTION_LOCK_V2.md` §10, §11, §12, §13, §23A, §27 (G1–G4), Phase 0 build order.
**Question being stress-tested:** kya normal Android smartphone par calibrated planar printed-glyph height ko mm mein reliably estimate, uncertainty quantify, aur unsafe condition par abstain kiya ja sakta hai?

**Verdict headline:** Phase 0 **physically feasible hai**, but V2 ka current Phase-0 design **wrong error terms par rigor kharch kar raha hai**. Jo cheezein V2 sabse zyada tight kar raha hai (CMM-surveyed frame, 0.10 mm absolute flatness, 1000-sample on-device Monte Carlo) woh error budget mein **near-negligible** hain. Jo terms actually dominate karte hain (ink-edge/threshold definition bias, phone ISP sharpening, per-device bias, glyph apex estimator, depth-of-field) unhe V2 either implicitly handle karta hai ya miss karta hai.

Saare numbers hypotheses/targets hain. Neeche ke calculations first-order optics/propagation analysis hain — experimental results nahi.

---

## POST-IMPLEMENTATION CORRECTIONS (added by the consistency audit)

This review was written **before** the P0-min code existed. It is kept as the design
record. Five of its recommendations were later changed or falsified by the executed
synthetic experiment (`phase0/out/synthetic`). Where they differ, the code,
`phase0/config/*.json` and `phase0/docs/P0_ASSUMPTIONS.md` are authoritative.

| Recommendation in this document | What actually happened |
|---|---|
| §F2.4 / §20.8 frame outer **150 x 90 mm**, window 100 x 30 mm | Built at **100 x 60 mm**, window 50 x 20 mm, marker 10 mm. Reason: rendering cost and keeping the whole frame inside the synthetic image at rho = 18 px/mm. |
| §0.3 / §F2.1 "replace the flatness gate with **local tilt <= 5 deg**" | **Only partly implementable.** Local print-plane tilt relative to the fiducial plane is *not observable from one view* — measured, see `P0_ASSUMPTIONS.md` A-06: a 20 deg local tilt produced a 0.185 mm error while reprojection RMS stayed at 0.09 px and LOMO at 0.0002. The shipped gate `max_view_tilt_deg = 30` measures **view obliqueness**, a different quantity. Local tilt is carried as a bounded budget term (`residual_tilt_bound_deg = 3.0`, not 5.0) and must be guaranteed by the fixture. |
| §20 / verdict #23, #32 "**rho >= 12 px/mm**" | Too low. The pre-registered blur gate (sigma <= 0.06 mm) is unreachable below roughly 15-16 px/mm with a realistic PSF, so `P0_PROTOCOL.md` §4 sets the *capture target* at **>= 16 px/mm**. The shipped gate floor stays at **10.0** — it was pre-registered and was not moved after seeing results. |
| §15 / §16 reference-measure "**60 glyphs**" (3 per coupon) | The generated coupons carry 4 shapes x 5 heights per panel, so the pilot has **400 glyph instances** across 20 panels. The microscope cross-check subset remains >= 15. |
| §F2.2 use a **ChArUco border** for control points | Not built — cv2.aruco is unavailable offline. NDFID-1 coded squares with subpixel edge-line corners are used instead (A-03). The metrological principle is preserved; absolute corner performance versus ChArUco is untested. |

Two items in §18 were also resolved by measurement rather than by design:
`u_photometric` / `u_device_residual` are **not separate budget fields** (they share the
single `u_extra_mm` slot, currently 0.0), and focal-length error turned out **not** to
bias the height at all, because metric scale comes from the surveyed fiducial (A-08).

---

## 0. Numeric reality check (assumption: 12 MP main camera, 4000 px across, ~67° HFOV, f≈6 mm, f/1.8)

| Working distance Z | FOV width | ρ (px/mm) | px per 3 mm glyph | DOF (CoC 2 µm) | DOF (CoC 5 µm) |
|---:|---:|---:|---:|---:|---:|
| 100 mm | 132 mm | 30.2 | 91 | 2.0 mm | 5.0 mm |
| 150 mm | 199 mm | 20.1 | 60 | 4.5 mm | 11.2 mm |
| 200 mm | 265 mm | 15.1 | 45 | 8.0 mm | 20.0 mm |
| 250 mm | 331 mm | 12.1 | 36 | 12.5 mm | 31.3 mm |
| 300 mm | 397 mm | 10.1 | 30 | 18.0 mm | 45.0 mm |

### First-order error contributions on a 3.00 mm glyph

| Term | Magnitude | Error on 3 mm glyph | Verdict |
|---|---|---:|---|
| Frame survey with **caliper** (u=0.02 mm over 120 mm baseline) | 0.017% | **0.0005 mm** | negligible |
| Frame survey with 0.5 mm error over 120 mm | 0.42% | 0.013 mm | still small |
| Frame thickness offset d=0.5 mm at Z=150 mm | 0.33% | **0.010 mm** | small, and exactly correctable |
| Carton bow sagitta 1.0 mm at Z=200 mm | 0.50% | 0.015 mm | small |
| Local panel **tilt** α=5° | 0.38% | 0.011 mm | small |
| Local panel **tilt** α=15° | 3.4% | **0.102 mm** | significant |
| Edge localization 0.2 px/edge at ρ=12 px/mm | — | 0.024 mm | small |
| Edge localization 1.0 px/edge at ρ=8 px/mm | — | **0.177 mm** | dominant if blurry/low ρ |
| Ink spread + 50% threshold definition + ISP sharpening bias | 0.5–2 px systematic | **0.04–0.25 mm** | **DOMINANT, uncontrolled** |

### Three conclusions that change Phase 0

1. **Scale/reference chain is NOT the bottleneck.** V2 ka CMM/optical-comparator survey requirement over-engineered hai. Calibrated digital caliper (0.02 mm) already 0.0005 mm contribute karta hai — target MAE (0.15 mm) se 300× chhota. CMM ko "nice to have" banao, blocker nahi.
2. **Absolute flatness gate (≤0.10 mm) physically wrong metric hai.** Jo matter karta hai woh `d/Z` (offset/distance ratio) aur **local tilt α** hai. 1 mm bow ka effect 0.015 mm hai; 15° local tilt ka effect 0.102 mm hai. Isliye spec ko "≤0.10 mm flatness" se "local tilt ≤5° + known thickness correction + LOMO scale consistency" mein badalna chahiye. Bonus: ye achievable hai, jabki 0.10 mm absolute gate ek card frame ke saath **structurally impossible** hai (card thickness hi 0.3–0.5 mm hoti hai).
3. **Dominant error photometric hai, geometric nahi.** Glyph height ka actual limit ink spread, print gain, PSF asymmetry aur phone ISP sharpening/halo hai. Ye terms ρ badhane se kam **nahi** hote; sirf empirical bias calibration + gates se control hote hain. Isliye Phase 0 ka real experiment "homography kaam karti hai?" nahi — woh trivially kaam karegi — balki **"ink-boundary bias stable aur correctable hai across device/font/stock?"** hai.

---

## 1. Exact measurand definition

**Current V2:** "estimated visible printed-ink glyph extent perpendicular to fitted text baseline", 50% transition contour, `h = max(n·p) − min(n·p)`.

### Findings

- **F1.1 — `max − min` ek biased estimator hai. [mathematically weak]**
  Extreme-value statistics: noise ke saath max upward aur min downward move karte hain, so `h` systematically **inflate** hota hai, aur bias noise level ke saath badhta hai — i.e. blurrier/noisier capture par glyph *bada* dikhega. Ye "safe" direction hai false-accusation ke liye but false-clear ke liye unsafe, aur device-dependent bias inject karta hai.
  **Fix:** per-scanline subpixel 50% crossings nikaalo, phir top edge aur bottom edge par **model fit** karo (flat-top glyphs ke liye robust line; round glyphs ke liye apex ke paas parabola), aur fitted extremes ka distance lo. Ye estimator variance ko ~1/√N se reduce karta hai aur extreme-value bias hata deta hai.

- **F1.2 — 50% threshold gamma-encoded pixels par apply karna mathematically galat hai. [mathematically wrong]**
  Agar mapping `g` non-affine (sRGB gamma) hai, to `g(I) = (g(I_paper)+g(I_ink))/2` wala point `I = (I_paper+I_ink)/2` wale point se different hota hai. Ink dark hone ke kaaran gamma asymmetric compression karta hai → systematic edge shift, jo contrast ke saath badalta hai. V2 isko specify nahi karta.
  **Fix:** sRGB EOTF se linearize karo (ya at least ek fixed documented decode), phir 50% lo. Aur `linearization_version` ko measurand policy ka part banao.

- **F1.3 — contrast gate "≥50 levels on 8-bit" ill-defined hai.**
  Linear vs encoded space specify nahi; aur absolute level difference low-brightness region mein meaningless hai.
  **Fix:** Weber/Michelson contrast in linear space, e.g. `(L_paper − L_ink)/(L_paper + L_ink) ≥ 0.30`, plus minimum SNR (local noise sigma se ratio).

- **F1.4 — "visible printed-ink extent" ≠ legal character height. [scientifically unsupported as legal measurand]**
  Ink spread/dot gain se printed ink extent designed cap-height se typically bada hota hai. V2 ne isko G0 mein flag kiya hai — correct — but Phase 0 mein isse **do alag numbers** treat karna chahiye: `h_ink_50` (measurable) aur `h_nominal` (unknown mapping). Phase 0 sirf pehla claim kar sakta hai.

- **F1.5 — eligible glyph class undefined.** Descender/ascender/accent/punctuation/dot-on-i shamil honge ya nahi, V2 "eligible glyphs" bolta hai but policy define nahi karta. Phase 0 ke liye **explicit whitelist** chahiye.

**Verdict:** NEEDS MODIFICATION (estimator + linearization + contrast definition + glyph whitelist).

---

## 2. Physical reference frame design

**Current V2:** matte rigid serialized frame, central cut-out, 4 ArUco markers, surveyed coordinates, ROI inside hull, ≤0.10 mm plane offset/flatness.

### Findings

- **F2.1 — ≤0.10 mm plane-offset gate chosen fixture ke saath self-contradictory hai. [impractical]**
  Package face par rakha gaya frame apne thickness ke barabar offset banata hai. 300 gsm card ≈ 0.4 mm; acrylic 2–3 mm. Gate din ke pehle capture mein hi fail karega, ya team gate ko "visually declared" karke jhooth bol degi.
  **Fix:** offset ko **measure aur correct** karo, gate na banao:
  `h_corrected = h_measured × (1 + d / Z_marker)`, where `d` = frame thickness (caliper, once, ±0.01 mm), `Z_marker = f_px / ρ` (homography + intrinsics se computable).
  Residual gate: `d/Z ≤ 1%` (i.e. `Z ≥ 100 d`), plus `u(d)/Z` ko budget mein daalo.

- **F2.2 — ArUco square corners geometry ke liye second-best hain. [engineering weakness]**
  Marker corner localization typically 0.1–0.3 px, jabki checkerboard (saddle-point) corners generally better-conditioned hote hain kyunki unka estimate do intersecting edges se aata hai, single quad fit se nahi.
  **Fix:** **ChArUco-style border** use karo: markers sirf ID/serial/orientation ke liye, actual control points chessboard corners. Ye ~2–4× zyada control points bhi deta hai, jo LOMO aur residual diagnostics strengthen karta hai.

- **F2.3 — printed paper frame ka dominant risk dimensional instability hai, survey uncertainty nahi.**
  Laser printer scaling error 0.2–1% ho sakta hai, aur paper humidity se move karta hai. **Survey isko pakad leta hai** (ek baar), so printing acceptable hai — but **material matters**: polyester/mylar film ya laser-engraved acrylic/aluminium >> plain paper. Paper par stick karna ho to rigid board par flush laminate karo.

- **F2.4 — frame size ka DOF trade-off V2 mein absent hai. [critical practical gap]**
  Bada frame → bada Z chahiye → ρ girta hai; chhota frame → chhota Z → DOF collapse. 100 mm par DOF ≈ 2–5 mm only.
  **Recommended Phase-0 geometry:** frame outer ≈ **150 × 90 mm**, measurement window ≈ 100 × 30 mm, marker/checker band 20 mm, working distance **Z ≈ 180–240 mm**, giving **ρ ≈ 12–17 px/mm** (3 mm glyph → 36–50 px) with DOF ≈ 6–18 mm. Ye focus-safe aur accuracy-sufficient dono hai.

- **F2.5 — frame serial/identity spoofing.** Marker ID set hi frame identity hona chahiye: dictionary + expected ID tuple + serial hash. Wrong/duplicate frame ko hard-fail karo.

**Verdict:** NEEDS MODIFICATION (offset correction instead of impossible gate, ChArUco control points, explicit frame geometry, material spec).

---

## 3. Camera calibration

**Current V2:** per device + camera + resolution + zoom/focus profile, ChArUco ≥20 views, Brown–Conrady, expiry on setting change.

### Findings

- **F3.1 — Kya intrinsic calibration Phase 0 mein zaroori bhi hai? [UNKNOWN — needs experiment]**
  Critical geometric insight: ROI ko **surround** karne wale 4-corner frame par fit ki gayi local homography low-order distortion ko largely **absorb** kar leti hai, kyunki hum sirf enclosed region interpolate kar rahe hain, extrapolate nahi. Residual error second-order hota hai. Isliye possible hai ki full per-device Brown–Conrady calibration ka net effect ≪ 0.02 mm ho — jo target ke against noise hai.
  **Action:** ye Phase 0 ka **Experiment E3** hai: same captures ko with/without undistortion process karo, Δh distribution report karo. Agar |Δh| P95 < 0.02 mm, to per-device intrinsics ko Phase 1+ ke liye defer kiya ja sakta hai (with a gate that ROI frame ke central 60% mein rahe). Ye **sabse bada possible simplification** hai — but claim karne se pehle measure karna mandatory.

- **F3.2 — OIS silently calibration todta hai. [practical, high risk]**
  Optical image stabilization lens elements shift karta hai → per-frame effective principal point/distortion badalta hai. Phone par ye ek real, often-ignored metrology killer hai.
  **Fix:** capture ke waqt OIS/EIS explicitly OFF karne ki koshish karo (`LENS_OPTICAL_STABILIZATION_MODE_OFF`, `CONTROL_VIDEO_STABILIZATION_MODE_OFF`); support na ho to device ko "OIS-uncompensated" mark karo aur burst-spread se uska variance capture karo.

- **F3.3 — focus breathing.** AF distance ke saath effective focal length badalta hai. Isliye calibration **working-distance band** ke andar hona chahiye aur runtime par Z band enforce karna chahiye.

- **F3.4 — "macro mode" trap. [critical practical]**
  Kai Android phones close-focus par silently **different physical camera** (ultra-wide/macro) par switch karte hain — bilkul different intrinsics, much higher distortion, lower resolution. Agar app camera ID pin nahi karega to calibration invisible ho kar invalid ho jayegi.
  **Fix:** physical camera ID + resolution + AF mode pin karo, log karo, aur mismatch par hard abstain karo.

- **F3.5 — covariance source.** V2 "intrinsic covariance" maangta hai; OpenCV `calibrateCamera` full covariance nahi deta (`calibrateCameraExtended` sirf std deviations deta hai). Practical route: calibration images par **bootstrap** (e.g. 200 resamples) → empirical parameter covariance.

**Verdict:** NEEDS MODIFICATION + UNKNOWN (necessity must be measured, OIS/camera-ID handling must be added).

---

## 4. Marker detection

- **F4.1** OpenCV 4.7+ mein API `cv::aruco::ArucoDetector` / `CharucoDetector` hai; purana `cv::aruco::detectMarkers` free-function deprecated path hai. Version pin karo, warna refinement behaviour chup-chaap badal jayega aur results reproducible nahi rahenge.
- **F4.2** `CORNER_REFINE_SUBPIX` window size ρ ke saath scale hona chahiye; fixed window low-ρ par under-refine aur high-ρ par neighbouring structure pick karega.
- **F4.3** Strong perspective/blur mein ArUco corners biased hote hain — isliye F2.2 (chessboard control points) recommended.
- **F4.4** Required: detected ID set == expected frame ID set (exact match), koi extra/duplicate marker nahi, aur har marker ka quad convexity/aspect sane ho.

**Verdict:** NEEDS MODIFICATION (control-point source + version pinning + ID-set strictness).

---

## 5. Homography

- **F5.1 — Normalized DLT + LM refinement correct hai.** `p_plane = normalize(H⁻¹ p_img)` bhi correct hai.
- **F5.2 — Cost function mismatch. [minor mathematical]** Image-space reprojection minimize karna measurement-space accuracy ko directly optimize nahi karta. Better: symmetric transfer error, ya plane-space weighted error. Practically chhota effect, but document karo.
- **F5.3 — RMS ≤0.25 px as a *planarity* proxy weak hai.** 16 points, 8 DOF → low residual easily achievable even with real out-of-plane geometry. V2 khud ye bolta hai (§12.3) — good — but phir bhi gate list mein RMS ko planarity evidence jaisa treat kiya gaya hai. Explicitly separate karo: RMS = *fit consistency*, LOMO = *scale consistency*, tilt/thickness = *geometry model*.
- **F5.4 — LOMO with only 4 marker groups ka statistical power low hai.** ChArUco border ke saath sub-region based LOMO (e.g. 6–8 groups) zyada meaningful hai.

**Verdict:** PASS with modification (keep method; strengthen diagnostics, stop treating RMS as planarity proof).

---

## 6. Perspective / distortion handling

- **F6.1 — "undistort points, not image" decision correct aur important hai.** Rectified bitmap par measure karna resampling bias introduce karta hai. Isse rakho.
- **F6.2 — Order of operations must be frozen:** contour extraction **distorted raw luma** par (intensity distortion se change nahi hoti), phir `undistortPoints`, phir `H⁻¹`. V2 implies karta hai, spec mein explicit karo.
- **F6.3 — `cv::undistortPoints` iterative hai;** iteration count/termination OpenCV version-dependent → reproducibility ke liye version pin karo aur tolerance define karo.

**Verdict:** PASS (order ko normative banao).

---

## 7. Glyph segmentation

- **F7.1 — Full contour + connected-component + topology-stability approach Phase 0 ke liye over-engineered aur fragile hai. [impractical for scope]**
  Touching glyphs, anti-aliasing, halftone fill, outlined text, dot-on-i, accents — ye sab CC logic ko todte hain, aur V2 ka "40/50/60% topology stable" gate inko reject karega, jisse abstention rate demo-killing level tak ja sakta hai.
  **Fix (Phase 0 simplification):** operator ek glyph select karta hai (tap/box). System us box mein **baseline-normal direction ke along N scanlines** (N ≈ 20–40) lega, har scanline par top aur bottom 50% crossing subpixel nikalega, phir top/bottom edge models fit karega. **Koi morphology, koi CC labelling, koi topology test nahi.** Ye simpler, more accurate aur far more testable hai.
- **F7.2 — Round-glyph apex.** 'O','0','8','S' ka top ek curve hai; line fit galat hoga. Apex ke ±30% width region mein **parabola fit** karo aur vertex lo. Flat-top glyphs ('H','E','T','I','1','7','N') ke liye robust line fit.
- **F7.3 — Stroke-interaction limit.** Blur σ agar stroke gap ke comparable ho jaye to 50% crossing shift hota hai. Isliye physical gates: `σ_blur ≤ 0.06 mm` aur `stroke width ≥ 4 px`. (Note: **symmetric defocus 50% crossing ko largely preserve karta hai** — isliye moderate blur bias se zyada *noise* aur *interaction* problem hai. Ye important nuance V2 mein missing hai.)
- **F7.4 — ISP sharpening halos asymmetric overshoot banate hain → real bias.** Detect: edge profile mein pre-edge undershoot/post-edge overshoot ratio measure karo; threshold cross karne par abstain ya bias-corrected device profile use karo.

**Verdict:** NEEDS MODIFICATION (scanline estimator replaces contour/CC pipeline for Phase 0).

---

## 8. Source-image → metric mapping

**Verdict:** PASS. Formula, inverse-homography mapping, aur no-resampling rule sahi hain. Sirf itna add karo: mapping ke baad **thickness correction (F2.1)** apply ho, aur har mapped point ka `Z` estimate log ho.

---

## 9. Uncertainty estimation

- **F9.1 — 1000-sample per-capture Monte Carlo on-device: feasible but wrong priority. [practical + scientific]**
  Native OpenCV mein 1000 × (16-point homography refit + ~1000 point maps) roughly 0.2–0.6 s hai, so *feasible*. Lekin MC sirf **modelled** terms propagate karta hai; dominant term (ink/threshold/ISP bias) model mein hi nahi hai. Result: ek precise-looking interval jo actual error ko under-represent karega → **false confidence**, exactly jo V2 avoid karna chahta hai.
  **Fix (recommended architecture change):** device par MC ki jagah **empirically calibrated closed-form uncertainty model** use karo, aur MC ko offline analysis tool rakho:
  ```
  u_c² = u_burst²            (live, measured from a 5–9 frame burst)
       + u_scale²            (live, from LOMO scale spread)
       + u_geom²             (live, from d/Z, tilt proxy, Z band)
       + u_photometric²      (offline-validated, function of ρ, edge-spread, contrast, overshoot)
       + u_device_residual²  (offline-validated per device class)
  ```
  **Burst-based `u_burst` sabse valuable addition hai:** 5–9 frames ka spread operator shake, AF jitter, OIS drift, ISP variance sabko *directly measure* karta hai, bina modelling assumptions ke. Ye cheap, honest aur defensible hai.

- **F9.2 — Quadrature mein bias mila dena galat hai. [mathematically wrong]**
  `u_model` agar validation ke against *residual bias* hai to woh systematic hai: use **correct** karna chahiye aur sirf correction ki uncertainty combine karni chahiye. Bounded systematic terms (thickness, threshold band) ko GUM-style rectangular distribution se convert karo: `u = a/√3`. V2 ka "largest deviation se interval expand karo" conservative hai but phir usko "95% interval" kehna galat hai.

- **F9.3 — Correlated vs independent terms aur "minimum glyph" rule. [mathematically important]**
  Do alag problems hain, V2 dono miss karta hai:
  (a) **Min ka selection bias:** noisy estimates ka minimum true minimum se systematically neeche hota hai, aur ye bias glyph count aur per-glyph noise ke saath badhta hai. Isse `POTENTIAL_UNDERSIZE` ki taraf tilt aata hai — i.e. **false-accusation risk**.
  (b) **Uncertainty structure:** scale/geometry error saare glyphs par **common-mode** hai, jabki edge noise per-glyph independent hai. Dono ko ek hi quadrature mein daal dene se min ke bound galat nikalte hain.
  **Fix:** per-glyph `u_edge` aur common-mode `u_common` alag rakho; deciding glyph min *bias-corrected* values par choose karo; uska bound `sqrt(u_common² + u_edge²)` se banao (common-mode ek hi baar); per-glyph noise ko zyada glyph average karke kam karo; aur agar deciding glyph baaki distribution ka robust outlier hai to `REQUIRES_OFFICER_REVIEW` (probable estimator/segmentation fault), silently `POTENTIAL_UNDERSIZE` nahi.

- **F9.4 — `k` aur bias correction same data par fit karna optimistic hai.** Development set par freeze, sealed set par evaluate — V2 ye bolta hai, spec mein enforce karo (custodian + preregistration).

- **F9.5 — SHA-256-seeded MC "deterministic replay" ka claim overstated hai. [scientifically unsupported]**
  Cross-device/cross-ABI floating-point, libm, NEON vs x86, OpenCV build flags → bit-identical results guaranteed nahi. Claim ko "same binary + same ABI par bit-identical; otherwise replay tolerance |Δh| ≤ 0.005 mm" tak limit karo, aur MC outputs ko evidence mein **store** karo (recompute par depend na karo).

**Verdict:** NEEDS MODIFICATION (replace on-device MC with burst + calibrated model; fix bias/quadrature; fix correlation; soften determinism claim).

---

## 10. Guard-band decision

- **F10.1 — Interval semantics ambiguous hain.** `L ≥ T` pass aur `U < T` fail ko two-sided 95% interval ke saath use karna error rates ko implicit chhod deta hai.
  **Fix:** explicitly define: `L` = one-sided 95% lower bound, `U` = one-sided 95% upper bound; state karo ki `[L,U]` ek 90% two-sided region hai; aur false-accusation-critical side par 99% use karne ka option policy mein rakho.
- **F10.2 — Width gate `U−L ≤ max(0.10 mm, 0.15T)` internally inconsistent hai. [mathematically inconsistent]**
  T = 1.0 mm par gate = 0.15 mm width (±0.075 mm). Lekin V2 ka own accuracy target P95 = 0.30 mm hai — us accuracy ke consistent interval ~0.6 mm wide hoga. Matlab chhote T par gate **sab kuch abstain** kar dega. Reverse case: T = 3 mm par gate 0.45 mm — itna loose ki practically bind hi nahi karega.
  **Fix:** width gate ko arbitrary formula se hatao; use `U−L ≤ β × u_validated(ρ, blur, contrast)` with β frozen after pilot, plus absolute floor for demo sanity. Gate ko **validated uncertainty ka function** banao, independent constant nahi.
- **F10.3 — No-rounding rule:** PASS, keep.

**Verdict:** NEEDS MODIFICATION (bound semantics + width gate derivation).

---

## 11. Abstention logic

- **F11.1** State machine structure PASS. Monotonic gating, reason codes, stale-result invalidation — sab sahi hai.
- **F11.2 — Missing gates jo add karne chahiye:**
  - **paper-side highlight clipping** (sirf ink saturation check karna adhura hai; 50% level dono levels par depend karta hai);
  - **burst consistency** (5–9 frames par height spread > limit → abstain; motion/OIS/AF instability ko pakadta hai);
  - **overshoot/halo ratio** (ISP sharpening bias detector);
  - **camera-identity/settings match** (F3.4);
  - **Z-band check** (calibration working-distance band ke andar).
- **F11.3 — Abstention gaming risk.** "Loosen the gates till the demo passes" sabse likely failure mode hai. Isliye gates ko signed, versioned policy file mein rakho aur har result mein `policy_hash` store karo; pilot ke baad koi bhi loosening = sealed set reset.
- **F11.4 — Coverage/risk reporting mandatory.** Abstention rate ke bina accuracy meaningless hai; dono saath report karo (selective-risk curve).

**Verdict:** PASS with additions.

---

## 12. Failure cases (Phase-0 relevant, ranked by expected damage)

| # | Failure | Mechanism | Detection | Containment |
|---|---|---|---|---|
| 1 | ISP sharpening/denoise edge bias | computational photography | overshoot ratio, device profile | RAW/minimal-processing capture; per-device bias; abstain |
| 2 | Ink spread / dot gain | printing physics | bias vs reference | measure & correct; report measurand honestly |
| 3 | Gamma-unlinearized threshold | wrong math | synthetic fixture | linearize (F1.2) |
| 4 | `max−min` noise inflation | extreme-value bias | synthetic noise sweep | model-fit estimator (F1.1) |
| 5 | Macro/ultrawide camera switch | Android camera selection | camera ID log | pin camera ID; hard abstain |
| 6 | OIS drift | lens shift | burst spread | OIS off; burst gate |
| 7 | Shallow DOF at close range | optics | edge-spread gate | Z ≈ 180–240 mm; limit tilt |
| 8 | Frame thickness offset | fixture geometry | known d, computed Z | correction (F2.1) |
| 9 | Local panel tilt >10° | carton not flat | frame rock/gap, LOMO | flat backing; abstain |
| 10 | Printed frame scaling error | printer/paper | one-time survey | survey + serial binding |
| 11 | Wrong/expired frame | operator | ID-set + serial + expiry | hard abstain |
| 12 | Touching/outlined/halftone glyphs | typography | profile shape checks | out of Phase-0 scope; abstain |
| 13 | Glare on measured edge | specular | saturation mask | abstain; re-angle |
| 14 | Motion blur | handheld | edge spread, burst | abstain |
| 15 | Operator picks different glyph | protocol | log glyph identity | deterministic selection policy |
| 16 | JPEG ringing | compression | quality/RAW check | highest quality or RAW |
| 17 | Near-threshold overconfidence | uncalibrated interval | coverage test | guard band + review state |
| 18 | Post-hoc gate loosening | process | policy hash | freeze + sealed reset |

---

## 13. Phone-to-phone variability

- **F13.1** Har phone ka ISP different sharpening/denoise karta hai → **bias per device different hoga**, aur ye Phase 0 ka sabse likely "claim breaker" hai. Agar inter-device bias spread target se bada nikla, to claim "per-device-calibrated measurement" ban jayega, "universal smartphone measurement" nahi — jo honest but weaker positioning hai.
- **F13.2** RAW (DNG) availability device-dependent hai (`CameraCharacteristics` RAW capability). Mid-range devices par often absent/limited. Isliye Phase 0 mein **RAW vs JPEG dono** test karna chahiye aur delta report karna chahiye.
- **F13.3** Phase 0 scope: exactly **2 devices** (ek flagship-ish, ek mid-range), aur "supported device list" concept se hi shuru karo. Universal claim kabhi nahi.

**Verdict:** NEEDS EXPERIMENT (device effect size unknown, decides the claim wording).

---

## 14. Operator variability

- **F14.1** Variance sources: working distance, tilt, frame placement/press, glare angle, **glyph selection**, kitne frames.
- **F14.2** Fix: live capture assistant jo ρ, tilt proxy, edge-spread, contrast aur frame-ID sab green hone par hi shutter enable kare. Ye operator variance ko design se kam karta hai (aur demo mein bhi impressive hai).
- **F14.3** Glyph selection ko protocol banao: "measure the numeral/letter specified by the policy in the selected line; log glyph index + label". Warna operator-to-operator difference measurand hi badal degi.

**Verdict:** NEEDS MODIFICATION (add assisted capture + deterministic glyph policy).

---

## 15. Ground-truth measurement methodology

Ye Phase 0 ka **sabse underspecified** part hai — aur iske bina G2/G3 impossible hain.

| Option | Resolution | Practicality | Verdict |
|---|---|---|---|
| Toolmaker's/measuring microscope with micrometer stage (college mech lab) | ~1–2 µm stage | medium (lab access) | **Preferred primary** |
| Flatbed scanner @2400 dpi (94.5 px/mm) + calibrated graticule/steel scale | ~0.01 mm | **high** — cheap, repeatable | **Recommended primary for a student team** |
| USB digital microscope + calibration slide | ~0.01 mm | high | acceptable secondary |
| Vernier/digital caliper on a 3 mm printed glyph | — | not applicable to ink boundary | **REJECT** |
| Nominal design height from the PDF/artwork | — | printer scaling unknown | **REJECT as ground truth** |

**Critical requirements:**
1. Ground truth **same measurand** implement kare: linearized 50% ink boundary + same estimator, sirf ~6–8× higher ρ. Warna aap do different quantities compare kar rahe ho.
2. Scanner ka scale **independently calibrate** ho (calibrated steel scale/graticule, both axes), aur non-uniformity map ho.
3. **Cross-method check:** 15–20 coupons ko scanner aur microscope dono se measure karo; agar inter-method difference target uncertainty ke ~1/3 se bada hai, to accuracy claim usi tak limit hoga.
4. Test-uncertainty-ratio: reference expanded uncertainty ≤ (1/3) × system target. Scanner ~0.01 mm vs system 0.15 mm → ratio comfortable.

**Verdict:** NEEDS MODIFICATION (V2 ka microscope-only requirement replace/supplement with calibrated-scanner protocol, plus cross-method validation).

---

## 16. 20-panel pilot design (V2 Phase 0 step 5)

**F16.1 — V2 ka "20-panel pilot" ka purpose V2 mein under-defined hai, aur 20 panels se coverage validate karna impossible hai.** Pilot sirf ye answer kar sakta hai: repeatability, bias magnitude/stability, device effect, gate acceptance rate, aur "kya aage badhna chahiye".

### Locked pilot design (P0-PILOT)

- **Panels:** 20 printed coupons, ek hi rigid flat plate par mounted.
  - 4 font families × 5 nominal heights spanning ~1.2, 2.0, 3.0, 4.0, 6.0 mm.
  - 2 stocks (matte/semi-gloss) distributed across panels.
  - Har coupon par 3 eligible glyphs (1 flat-top, 1 round, 1 numeral).
- **Reference:** har glyph scanner-measured (+ 20% subset microscope-cross-checked).
- **Captures:** 20 panels × 2 devices × 2 operators × 3 repeats = **240 captures**; angles repeats ke across assigned (0°, 12°, 25°), plus ek separate stress block (35°, glare, motion, wrong frame, tilted panel) = ~60 captures.
- **Each capture = burst of 7 frames** (burst uncertainty ke liye).
- **Processing:** with/without undistortion (E3); RAW vs JPEG jahan available (E4); `max−min` vs model-fit estimator (E1); gamma vs linearized threshold (E2).

### Pilot analysis (preregistered)

1. Per-glyph signed error vs reference; bias by device/font/stock/height/angle.
2. Repeatability SD: within (panel, device, operator); and between operators/devices.
3. Residual SD **after** a single global bias correction; then after per-device correction. Delta = device-effect evidence.
4. Gate acceptance rate per condition; abstention reason histogram.
5. `u_burst` vs actual error correlation — kya live burst spread error ka useful predictor hai?
6. Estimator/linearization/undistortion ablation deltas.

### Pilot go/no-go (numbers = hypotheses, pre-registered)

| Criterion | Go | Conditional | No-go |
|---|---|---|---|
| Residual SD after global bias correction (3 mm class) | ≤0.08 mm | 0.08–0.15 mm | >0.15 mm |
| Repeatability SD (same panel/device) | ≤0.05 mm | 0.05–0.10 mm | >0.10 mm |
| Inter-device bias after global correction | ≤0.05 mm | 0.05–0.12 mm | >0.12 mm → per-device claim only |
| Gate acceptance in nominal conditions | ≥70% | 50–70% | <50% → redesign fixture/protocol |
| Unsafe-condition acceptance (stress block) | ≤2% | 2–5% | >5% → abstention unsafe |
| Reference cross-method agreement | ≤0.03 mm | 0.03–0.06 mm | >0.06 mm → no accuracy claim |

**Conditional** = proceed but claim narrower scope (e.g. per-device, single font class, larger interval). **No-go** = measurement claim downgrade karo, Android measurement UI build **na** karo.

---

## 17. Required test fixtures

**F17.1 — V2 mein synthetic ground-truth harness missing hai. Ye sabse sasta aur sabse decisive fixture hai.** Synthetic renders mein true height **exactly** known hoti hai, so pipeline ka *mathematical* correctness physical uncertainty se independent verify ho jata hai. Ye pehla fixture hona chahiye, pilot se pehle.

| ID | Fixture | Purpose | Pass criterion (hypothesis) |
|---|---|---|---|
| FX-SYN-01 | Ideal synthetic: known H, no blur/noise, known glyph heights | math correctness | abs error ≤0.005 mm |
| FX-SYN-02 | Known Brown–Conrady distortion applied | undistortion correctness | ≤0.010 mm |
| FX-SYN-03 | Tilt sweep 0–40° | homography + sampling | ≤0.020 mm up to focus limit |
| FX-SYN-04 | Gaussian blur sweep σ = 0.2–2.0 px | blur→bias/noise characterization | bias curve documented; estimator stable |
| FX-SYN-05 | Noise sweep + `max−min` vs model-fit | estimator-bias proof | model-fit bias < 1/3 of `max−min` bias |
| FX-SYN-06 | Gamma-encoded vs linear threshold | F1.2 proof | quantified shift documented |
| FX-SYN-07 | Simulated sharpening overshoot | ISP bias detector | detector flags ≥90% of injected cases |
| FX-SYN-08 | Off-plane offset d and tilt α injected | F2.1/F2.4 model proof | measured error matches d/Z and cos α prediction within 10% |
| FX-SYN-09 | Missing/duplicate/wrong marker | detection strictness | 100% hard-fail |
| FX-PHY-01 | Physical frame survey record + serial | reference chain | survey uncertainty documented |
| FX-PHY-02 | Control coupon (known glyph set) | daily control | within control limits |
| FX-PHY-03 | 20-panel pilot set + reference table | bias/repeatability | §16 criteria |
| FX-PHY-04 | Stress block (glare/motion/tilt/wrong frame/bowed panel) | abstention safety | unsafe acceptance ≤2% |
| FX-REG-01 | Golden capture set + expected JSON outputs | regression | byte/tolerance match |

---

## 18. Mathematical & engineering weaknesses — consolidated list

1. `max−min` extreme-value estimator → noise-dependent inflation. **(wrong estimator)**
2. 50% threshold on gamma-encoded values → contrast-dependent edge shift. **(wrong math)**
3. `u_model` (a bias) ko quadrature mein random term ki tarah daalna. **(wrong uncertainty treatment)**
4. Bounded systematic terms ko GUM divisor ke bina combine karna, phir "95%" kehna. **(unsupported claim)**
5. Common-mode scale error vs per-glyph noise ka distinction absent → min-over-glyphs rule biased. **(wrong risk model)**
6. Width gate `max(0.10 mm, 0.15T)` accuracy targets ke saath inconsistent (chhote T par sab abstain, bade T par gate inert). **(internal inconsistency)**
7. Absolute 0.10 mm plane/flatness gate physically wrong metric + chosen fixture ke saath impossible. **(wrong spec)**
8. Reference survey (CMM/optical comparator) over-specified; contribution ~0.0005 mm. **(misallocated rigor)**
9. "≥25 px per character" gate underspecified aur ρ/blur/stroke-width ke physical terms mein nahi. **(weak gate)**
10. Contrast gate "50 levels on 8-bit" undefined space. **(weak gate)**
11. Reprojection RMS ko implicitly planarity evidence ki tarah treat karna (doc ek jagah correct bolta hai, gate list mein contradict karta hai). **(inconsistency)**
12. SHA-256-seeded MC se cross-device bit-identical replay ka claim. **(unsupported)**
13. On-device 1000-sample MC ki precision **unmodelled dominant bias** ko chhupa kar false confidence banati hai. **(false-confidence risk)**
14. DOF/working-distance/tilt ka trade-off spec mein absent; 35° validation angle close range par focus-infeasible. **(missing physics)**
15. Macro/ultrawide camera auto-switch aur OIS ka calibration-invalidation risk unaddressed. **(missing platform reality)**
16. Ground-truth method (microscope-only) student-team ke liye fragile; scanner protocol absent; nominal design height ko GT maan lene ka risk. **(validation gap)**
17. §23A ka 450-panel × 3 recapture (+stress) = ~1550 microscope-referenced measurements SIH timeline mein infeasible. **(scope infeasibility)**
18. Glyph eligibility policy (descender/accent/round-apex) undefined → measurand ambiguous across operators. **(measurand gap)**
19. Legal measurand (`h_ink_50` vs nominal cap height) unresolved — correctly flagged in G0, but Phase 0 outputs ko do alag fields mein rakhna zaroori hai. **(reporting gap)**
20. Phase 0 ko Android app ke roop mein banane ka plan: highest-risk scientific question ko slowest development path ke peeche chhupa deta hai. **(sequencing error)**

---

## 19. Practical implementation complexity (honest estimate)

| Work item | Desktop (Python/OpenCV) | Android (Kotlin/JNI) |
|---|---|---|
| Frame design + fabrication + survey | 1–2 days (mostly waiting) | same artifact |
| Synthetic fixture harness | 1–2 days | reuse via golden JSON |
| Marker/ChArUco detect + homography + undistort | 0.5–1 day | 2–4 days (NDK, ABI, threading) |
| Scanline glyph estimator | 1–2 days | 2–3 days port |
| Uncertainty model + burst logic | 1–2 days | 2–3 days |
| Gates + state machine + JSON/logging | 1 day | 2–3 days |
| Camera calibration tool | 0.5 day | 2–4 days (in-app UX) |
| Capture app (assisted, locked settings, RAW/burst) | n/a | **3–6 days, highest platform risk** |
| Pilot execution + reference measurement | 2–4 days | same |
| Analysis/reporting scripts | 1–2 days | n/a |

**Conclusion:** Android par Phase 0 karne se ~2–3× time lagega aur scientific answer late milega. **Phase 0 ko desktop-first karo, phone ko sirf calibrated camera ki tarah use karo.**

---

## 20. What should be simplified for the SIH prototype

1. **Phase 0 = desktop analysis, not an app.** Phone se capture (locked settings, burst, RAW-if-available), files transfer, Python/OpenCV mein process. Port baad mein.
2. **Scanline estimator** (no contours, no morphology, no CC, no topology gate).
3. **Ek glyph, operator-selected**, policy-defined eligible class; per-glyph JSON.
4. **Caliper/scanner-based frame survey** (CMM optional), ChArUco border.
5. **Frame thickness ko correct karo**, flatness gate ki jagah tilt + d/Z gates.
6. **Burst-based live uncertainty + offline-calibrated photometric model**; on-device MC nahi (MC offline tool).
7. **Per-device intrinsics ki necessity pehle measure karo** (E3); possibly defer.
8. **Working distance band 180–240 mm**, tilt ≤25° nominal, 35° ko stress/abstention class banao (accuracy class nahi).
9. **Sealed set ko realistic karo:** e.g. 120 panels × 1 device-pair × 3 repeats, near-threshold oversampled, preregistered — 450-panel plan ko roadmap mein rakho.
10. **Demo case clearly-undersized rakho** (e.g. true ~2.2 mm vs T = 3.0 mm), near-threshold nahi, taaki guard band honestly conclusive rahe.
