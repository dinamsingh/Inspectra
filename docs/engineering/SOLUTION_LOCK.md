# SIH26034 — Inspectra
## SOLUTION LOCK V2 — Engineering Decision Baseline

**Status:** FROZEN for Phase 0–4 prototype implementation; statutory screening rules and performance claims remain disabled until the proof gates in §27 pass.  
**Language:** Hinglish; legal/CV terms intentionally English mein rakhe gaye hain taaki implementation ambiguity na ho.  
**Scope:** Ye final PPT nahi hai. Ye product, engineering, evidence aur validation contract hai.

> **Legal boundary:** Inspectra compliance-screening assistant hai, adjudication system nahi. Machine observations aur candidate findings banati hai; final legal determination authorised officer/authority ka rahega.

---

## Executive lock

Inspectra ko generic “AI + OCR + rules” scanner ke roop mein build **nahi** karna hai. Final product ek **offline-first field inspection assistant** hai jo controlled physical retail package inspection mein captured evidence ko dated rule version, calibrated physical character-height estimate, uncertainty, abstention aur officer review se jodta hai.

### Frozen decisions

| Decision | Final lock |
|---|---|
| Product | Android-based offline-first Legal Metrology field screening assistant |
| Primary user | Legal Metrology field officer/inspector |
| Primary scenario | Retail premises par ek rectangular, planar, printed carton ki inspection |
| Hero capability | Co-planar calibrated fiducial ke saath printed glyph height ko mm mein estimate karna, interval dena, aur evidence weak ho to refuse karna |
| Primary USP | **Evidence-bounded physical character-height screening: measurable conditions mein mm + uncertainty; otherwise explicit abstention; both source image aur rule version se linked** |
| Secondary differentiator | Independent multi-face coverage + cross-face/sticker contradiction preservation |
| Architectural differentiator | Immutable, source-linked, effective-date-aware rule packs + reproducible evidence lineage |
| AI boundary | OCR/extraction assistance only; MVP mein LLM required nahi |
| Legal output | Screening state, not legal verdict |
| Core operation | Capture se draft report tak fully offline |
| Cloud | Optional sync, backup, rule-pack distribution aur dashboard |
| MVP package class | Rectangular planar printed carton only |
| Hard exclusions | Curved/moulded measurement, photo-based net quantity truth, automated penalty/adjudication, marketplace crawling, medical-device rule adjudication |

### Adversarial conclusion

Competitor audit mein kisi capability ka “rare” hona moat prove nahi karta. Fiducial + homography ka demo ek competent team copy kar sakti hai. Defensibility **feature ke existence** se nahi, balki in accumulated assets se aayegi:

1. validated calibration fixture and protocol;
2. near-threshold physical benchmark with ground truth;
3. measured uncertainty coverage and abstention behaviour;
4. evidence-to-rule reproducibility;
5. maintained temporal rule corpus;
6. officer workflow integration.

Isliye PPT ka hero “hum font measure karte hain” nahi, balki “hum only supported conditions mein measure karte hain, error bound dikhate hain, aur unsupported condition mein claim refuse karte hain” hoga.

---

# 1. Final product definition

**Name:** Inspectra  
**Category:** Offline-first Legal Metrology field inspection and evidence assistant.  
**One-line definition:**

> **Inspectra officers ko package faces capture karke declarations screen karne, controlled planar print ka calibrated character-height estimate uncertainty ke saath dekhne, contradictions review karne, aur dated-rule/evidence-linked report banane mein assist karta hai—offline.**

Ye product teen layers ko explicitly separate karega:

1. **Observation:** image mein kya visible/read/measure hua.
2. **Screening inference:** applicable encoded rule ke against kya candidate issue hai.
3. **Officer determination:** officer ne evidence ko kaise accept, correct, reject ya escalate kiya.

### Why needed
Generic OCR “text found/not found” ko package-level truth bana deta hai. Master context ke evidence ke mutabik actual risk applicability, unseen faces, physical scale, amendments aur evidence traceability mein hai.

### What could fail
Agar calibration ya legal mapping weak hui to product sirf elaborate OCR app ban jayega. Agar workflow too slow hua to officer utility collapse hogi.

### Test
90-second controlled run, airplane mode, source crop → OCR span → normalized declaration → rule version → measurement → review → report trace complete hona chahiye.

---

# 2. Primary user

**Primary user:** State/UT Legal Metrology field officer conducting physical retail-package screening.

**Secondary future users:** supervisory reviewer, rules administrator, manufacturer pre-release compliance team, e-commerce audit team. Ye MVP personas nahi hain.

### Why officer first
Problem statement enforcement workflow ko target karta hai; field capture, uncertainty aur evidence chain officer context mein maximum value dete hain. Manufacturer artwork verifier easier hai lekin government workflow differentiation weaker hai.

### Assumptions to validate with users
- Officer rectangular package ke six face slots capture kar sakta hai.
- Calibration frame ko text ROI par temporarily flush place karna operationally acceptable hai.
- Package dimensions/manual category facts enter karne ka extra time acceptable hai.
- Draft screening report ka format useful hai.

**User test:** Kam se kam 3 domain reviewers/officers ko scripted prototype walkthrough; task completion, misunderstandings aur time record karna. Officer access na mile to legal-metrology faculty/practitioner proxy use karein aur limitation document karein.

---

# 3. Exact MVP scope

## 3.1 Real MVP — must actually work

1. Android app; one officer role; local PIN/biometric unlock.
2. Offline inspection creation with inspection date, place, SKU/batch, package archetype and applicability facts.
3. Rectangular carton ke six manually selected slots: front, back, left, right, top, bottom; optional `OVERLAY/STICKER` capture.
4. Capture quality checks: blur, glare/saturation, resolution, fiducial detection and geometry.
5. Original image preservation; derived rectified images/crops separately stored.
6. Offline OCR on selected Latin/Devanagari test set; raw text + alternatives + confidence retained.
7. Deterministic extraction for MRP, net quantity declaration, dates, responsible entity/contact, origin where applicable.
8. Signed local rule pack; inspection-date-based deterministic selection.
9. Controlled planar glyph measurement with serialized four-marker co-planar frame.
10. Measurement interval and explicit `PHYSICAL_SIZE_NOT_ESTABLISHED` failure reasons.
11. Cross-face MRP/net-quantity/date contradiction detection; sticker kept as separate layer.
12. Capture completeness independent from declaration completeness.
13. Mandatory officer review/correction/override reason.
14. Evidence-linked PDF + JSON report generated offline.
15. Local searchable history.
16. Optional server sync via outbox when network returns.

## 3.2 What prototype can prove **only after the corresponding §27 gate passes**

Neeche statements proof objectives hain; gate artifacts se pehle achieved capability nahi maane jayenge.

- A controlled planar printed region can be mapped from image pixels to physical millimetres using a surveyed co-planar reference.
- Estimate ke saath an empirical uncertainty interval and gate reasons can be produced.
- System insufficient geometry/evidence par abstain kar sakta hai.
- Multiple face observations can be preserved and compared without auto-resolving conflicts.
- A result can be replayed from frozen image hashes, extraction, rule pack and engine version.
- Core workflow can run without network.

## 3.3 What it must abstain from proving

- Curved, flexible, embossed, moulded, creased or unknown non-planar surfaces ka physical character size.
- Actual net quantity from a photograph.
- Whole-package declaration absence if required faces are incomplete/unreadable.
- Legal compliance where product classification, PDP determination, current threshold or exception is unresolved.
- Medical-device rule compliance.
- Sticker legality/chronology without officer evidence.
- Registration validity without authoritative access.
- Legally binding guilt, penalty or notice.

---

# 4. Final primary USP

> **Inspectra ka primary USP “calibrated physical measurement” alone nahi; “evidence-bounded planar character-height screening” hai: source-linked mm estimate + quantified uncertainty + guard-band decision, aur weak evidence par explicit refusal.**

### Why this wording
- OCR, PDF, dashboards, offline claims crowded/copyable hain.
- Homography alone bhi copyable hai.
- Measurement + empirical error model + abstention + traceability ek testable engineering claim hai.
- Officer ko false precision se bachata hai.

### Evidence supporting the decision
Master context identifies physical size as unsolved by pixel OCR, and explicit uncertainty/abstention as false-accusation reduction. Public audit mein universal absence prove nahi hui; therefore no “first/only/unique” claim.

### Failure mode
Agar ground-truth benchmark, calibration control aur interval coverage nahi dikhaya, USP invalid hai. Us case mein primary USP ko “evidence-linked offline workflow” tak downgrade karna hoga—less differentiated but honest.

### Acceptance test
§23 measurement benchmark aur §27 gates G1–G4 pass hone ke baad hi claim past tense mein jaayega.

---

# 5. Secondary differentiators

1. **Multi-face completeness separated from declaration completeness.** Six faces captured/readable hona ek fact; required field present hona separate fact. Is separation ke bina “missing declaration” logically unsafe hai.
2. **Cross-face and overlay contradiction graph.** Conflicting values both preserved; latest/high-confidence value silently choose nahi hota.
3. **Effective-date-aware source-linked rules.** Every evaluation exact rule version, source hash and inspection date store karta hai.
4. **Reproducible evidence chain.** Original → derivative → OCR span → declaration → evaluation → officer action → report.

Ye capabilities “rare/unique” nahi boli jayengi. Inhe supporting differentiation kaha jayega.

---

# 6. Supporting features

- Guided retake prompts.
- Raw OCR correction UI.
- Per-finding source crop and rule citation.
- Local inspection history/search.
- PDF and canonical JSON export.
- Optional GPS with accuracy; no mandatory location claim.
- Device/rule/calibration status screen.
- Sync health and conflict queue.
- Basic supervisor dashboard only after core proof.
- Accessibility: large controls, Hindi/English UI labels, offline help.

Supporting features moat nahi hain; build only after hero chain works.

---

# 7. Features to remove or defer

| Feature | Decision | Reason/fallback |
|---|---|---|
| Curved bottle/pouch measurement | Defer | Single homography invalid; return `PHYSICAL_SIZE_NOT_ESTABLISHED_NON_PLANAR` |
| Moulded/embossed glyph measurement | Remove from MVP | Edge definition and legal route unresolved |
| Actual net quantity verification | Defer | Requires verified instrument/sampling workflow; only label declaration screened |
| Medical-device detailed rules | Defer | Route to specialist regime; no generic PCR result |
| E-commerce crawling/filter audit | Defer | Separate functional mode, distracts from field MVP |
| Marketplace/package comparison | Defer | Keep architecture extensible, no demo dependency |
| Registration/Rule 33 live integration | Defer | Public/privileged API unknown; allow manual evidence attachment later |
| Cloud-first dashboard | Defer | Offline core and validation higher priority |
| LLM in decision path | Remove | Non-determinism, hallucination and offline burden; deterministic parser sufficient for MVP |
| Compliance percentage | Remove | Conceals missing evidence and unequal rule significance |
| Auto-generated legal notice/penalty | Remove | Unsafe legal conclusion |
| Blockchain | Remove | Does not establish evidence truth; adds no core value |
| Universal multilingual claim | Remove | Report only measured script/language subsets |
| Full automatic face classification | Defer | Manual slots are simpler and auditable |
| Automatic PDP legal determination | Defer | Officer marks candidate PDP; system records it as asserted fact |

---

# 8. End-to-end workflow

1. **Unlock & device check:** active rule pack, camera calibration profile, frame certificate and storage status shown.
2. **Create inspection:** date, location, package type, quantity band, retail/wholesale, domestic/imported, category, special-regime flags. Unknown allowed.
3. **Applicability pre-check:** unknown critical facts trigger `REQUIRES_OFFICER_REVIEW`; engine never assumes defaults.
4. **Guided face capture:** six slots plus overlay. Each image gets quality result, hash and metadata.
5. **Coverage review:** officer marks each required surface `CAPTURED_READABLE`, `CAPTURED_UNREADABLE`, `NOT_ACCESSIBLE`, or `NOT_APPLICABLE` with reason.
6. **OCR/extraction:** raw spans, alternatives and normalized candidates generated offline.
7. **Officer correction:** low-confidence spans and entity fields corrected before rule checks; original OCR retained.
8. **Declaration reconciliation:** observations grouped by field and scope; duplicates corroborate, incompatible values form contradiction.
9. **Measurement:** officer selects declaration line, places serialized frame co-planar, captures; system runs calibration/quality/geometry/segmentation/uncertainty gates.
10. **Rule evaluation:** inspection date + facts + frozen rule pack; four-valued predicate evaluation.
11. **Finding review:** each finding shows source crop, raw/normalized text, measurement interval, rule version and limitation.
12. **Officer action:** accept screening finding, correct observation, reject with reason, or escalate. No silent override.
13. **Report:** immutable report version generated; later correction creates superseding version.
14. **Local history:** searchable offline.
15. **Sync:** outbox uploads metadata/blobs when available; conflicts never last-write-win.

**Evaluator should notice:** airplane mode, face coverage, mm interval/abstention, two conflicting evidence cards, exact rule version, officer gate.

---

# 9. CV/OCR pipeline

## 9.1 Capture and CV stages

```text
CameraX RAW/JPEG capture
 → original hash + metadata
 → device calibration profile lookup
 → blur/glare/saturation/resolution gate
 → face-slot association (manual)
 → text detection + orientation
 → OCR alternatives
 → deterministic field parser
 → evidence spans
 → optional measurement branch
```

### Chosen stack
- **Client:** Kotlin + Jetpack Compose + CameraX.
- **CV:** OpenCV Android SDK.
- **OCR primary:** compact PaddleOCR-compatible detector/recognizer exported to ONNX Runtime Mobile, models bundled for selected scripts.
- **OCR backup:** Tesseract only if ONNX integration cannot meet device constraints; do not ship two engines in demo path.
- **Local persistence:** Room over SQLCipher-backed SQLite; encrypted file store.
- **Background work:** WorkManager.
- **PDF:** deterministic template rendered locally with pinned fonts; canonical JSON remains source of truth.

Package/library versions implementation start par pin honge; V2 document unverified “latest” versions claim nahi karta.

### OCR implementation contract

Before integration freeze: detector/recognizer ONNX SHA-256, source licence, script vocabulary, input size, quantization, preprocessing, operator-set compatibility and runtime version. Supported-device budget: offline inference median ≤3 s/face, P95 ≤6 s/face, peak incremental RAM ≤700 MB and model bundle ≤250 MB; miss par model/input size reduce ya supported-device list narrow hogi. Confidence raw probability ko legal confidence nahi maana jayega; development calibration curve se only review threshold derive hoga. Model swap new `model_version`, sealed OCR rerun and report provenance require karega. Tesseract fallback tabhi activate hoga jab primary integration Phase 0 mein fail declare ho; mixed-engine outputs same inspection mein silently merge nahi honge.

## 9.2 OCR rules

- OCR output observation hai, fact nahi.
- Store line polygon, raw text, per-character/line confidence if available, model ID/version and preprocessing parameters.
- MRP/quantity/date parsing deterministic typed grammar se.
- OCR correction new reviewed value banata hai; raw output overwrite nahi hota.
- Low-confidence critical field `UNKNOWN_OCR` or review; absence nahi.
- LLM MVP mein disabled. Future LLM output only span-linked candidate ho sakta hai; law/version/measurement/result choose nahi karega.

## 9.3 Likely failures and tests

| Failure | Containment | Test |
|---|---|---|
| Tiny text | Minimum pixels-per-glyph gate/retake | Distance/resolution sweep |
| Glare/foil | Saturation mask; abstain | Controlled glare angles |
| Blur | Edge/MTF proxy; retake | Motion/defocus set |
| Mixed script | Script-tagged model and metrics | Latin–Devanagari set |
| OCR “1/I”, “0/O” | Alternatives + field grammar + review | Seeded confusions |
| Decorative text | No field conclusion if unstable | Font stress set |
| Text on curve/fold | OCR may run; physical measurement blocked | Non-planar negatives |

---

# 10. Physical measurement algorithm

## 10.1 Exact measurand

MVP reports **estimated visible printed-ink glyph extent perpendicular to the fitted text baseline**, in millimetres, for explicitly selected eligible glyphs. It does **not** report font point size, nominal design size, OCR-box height or universal statutory “character height” unless legal measurement semantics are verified.

For contour points `p` mapped to package-plane millimetres and baseline normal unit vector `n`:

```text
h_glyph = max(n · p) - min(n · p)
```

Compliance aggregation is rule-specific. If rule means every eligible character must meet a minimum, use each glyph’s lower/upper interval and the minimum eligible glyph—not median. Median may be diagnostic only.

## 10.2 Geometry algorithm

1. Detect four coded markers and redundant marker corners.
2. Undistort source coordinates using camera profile.
3. Match detected corners to surveyed `(X_mm, Y_mm)` frame coordinates.
4. Fit normalized homography `H` with robust initialization and nonlinear refinement.
5. Require ROI inside marker-corner convex hull; no extrapolated measurement.
6. Detect text line; estimate baseline.
7. Estimate local ink/background levels; obtain 50% transition contour and 40%/60% sensitivity contours.
8. Map original-image subpixel contour points directly through `H⁻¹` into mm; do not depend on resized rectified bitmap dimensions.
9. Compute each glyph height and uncertainty.
10. Apply interval guard band against a verified/configured threshold.

```text
p_img ~ H · p_plane
p_plane = normalize(H^-1 · p_img)
```

## 10.3 Locked conservative per-capture gates

Ye **initial frozen safety gates** hain; pilot ke baad inhe loosen sirf sealed validation plan reset karke kiya ja sakta hai. Tightening allowed hai aur versioned policy record mein log hoga:

- All four marker IDs present; at least 12 valid surveyed corners.
- Homography reprojection RMS ≤0.25 px and max ≤0.60 px.
- ROI fully inside control-point hull with minimum margin `max(10 mm, 0.25 × ROI height)`.
- Leave-one-marker-out local-scale variation ≤0.5%.
- Applicable minimum height par at least 25 source pixels; local Jacobian singular-value ratio ≤3.
- Marker/text plane offset and local flatness deviation each ≤0.10 mm, verified by fixture control; visual declaration alone sufficient nahi.
- Fiducial 10–90% edge spread ≤1.5 px; measured contour par saturation/occlusion zero.
- 40/50/60% segmentation topology stable; touching, outlined, shadowed, broken or halftone glyphs validated extractor ke bina rejected.
- Expanded interval width `U-L ≤ max(0.10 mm, 0.15T)`; otherwise `PHYSICAL_SIZE_NOT_ESTABLISHED_UNCERTAINTY`.
- Correct frame serial, unexpired camera profile and passing same-day control coupon mandatory.

**Pilot escape rule:** Agar these gates usable captures ka <50% accept karein, team claim loosen nahi karegi; fixture/capture protocol redesign karegi aur sealed test reset karegi.

## 10.4 Threshold decision

For measured `h` and expanded interval `[L, U]` against minimum `T`:

```text
if legal measurand or T unresolved: REQUIRES_OFFICER_REVIEW
else if any quality/geometry/plane gate fails: PHYSICAL_SIZE_NOT_ESTABLISHED
else if L >= T: MEETS_SCREENING_THRESHOLD
else if U < T: POTENTIAL_UNDERSIZE
else: REQUIRES_OFFICER_REVIEW_BORDERLINE
```

No rounding before comparison.

---

# 11. Calibration method

## 11.1 Physical reference

**Frozen choice:** matte rigid serialized calibration frame with central cut-out and one ArUco marker near each corner. Text ROI must sit inside the marker coordinate hull. Frame package face par flush hona chahiye; adjacent ruler or another depth plane invalid hai.

For each frame store:

- `frame_id`, material, issue/expiry date;
- surveyed marker-corner `(x_mm,y_mm)` coordinates;
- survey instrument/method and uncertainty;
- flatness/coplanarity tolerance;
- certificate/artifact hash.

**Prototype practical path:** frame ko college metrology lab ke optical comparator/toolmaker microscope/CMM se survey karaya jaye. Calibrated digital caliper only fallback hai; fallback use hone par claim “controlled estimate” tak limited rahega, traceable/legal-grade nahi.

## 11.2 Camera calibration

- Har supported device + rear camera + resolution + zoom/focus profile separately calibrated.
- Rigid ChArUco board ke minimum 20 accepted views covering centre/corners/roll/working distance.
- Brown–Conrady distortion model; held-out reprojection and straight-line residual recorded.
- Capture settings locked and hashed.
- Calibration expires on camera/resolution/focus mode change, repair, or control-check failure.

## 11.3 Daily/control check

App start par known-dimension control coupon measure karega. Result certified value ke control limit mein na ho to measurement disabled, OCR workflow available, and status `CALIBRATION_CONTROL_FAILED`.

### What could fail
Printed marker nominal dimensions trusted, warped card, frame text plane se elevated, autofocus changes, bad corner localization.

### Test
Frame repeat survey; plane-offset challenge; three-angle control captures; deliberate wrong frame; camera-setting mismatch; leave-one-marker consistency.

---

# 12. Uncertainty model

## 12.1 Budget

```text
u_c² = u_ref² + u_camera² + u_marker/H² + u_seg²
       + u_baseline² + u_plane² + u_repeat² + u_model²
U95 = k × u_c
```

Where:
- `u_ref`: surveyed frame coordinate uncertainty;
- `u_camera`: intrinsic/distortion calibration covariance;
- `u_marker/H`: marker localization and homography fit;
- `u_seg`: 40/50/60% boundary sensitivity and edge localization;
- `u_baseline`: line-angle uncertainty;
- `u_plane`: allowed frame/package plane offset and flatness;
- `u_repeat`: operator/device repeated capture variation;
- `u_model`: residual error against ground truth.

## 12.2 Implementation

- Per capture, exactly 1,000 Monte Carlo samples; seed = SHA-256 of `(capture_hash + algorithm_version + policy_hash)` so replay deterministic ho.
- Camera intrinsic covariance, marker-corner localization and surveyed-coordinate covariance jointly sample honge; known correlations preserve ki jayengi. Unknown correlation ko independence assume karke hide nahi karna—validation residual `u_model` us gap ko cover karega.
- Segmentation threshold effect 40/60% contours se bounded systematic term hoga, Gaussian random term nahi.
- `u_plane` fixture ke measured ≤0.10 mm plane/flatness tolerance se bounded term hoga; unknown bow immediate abstention.
- Empirical validation residual added; bias correction only if development set par frozen and sealed test se pehle versioned.
- Nominal 95% interval ka acceptance tabhi jab sealed test par two-sided 95% confidence bound empirical coverage ko 90–98% band ke andar support kare; otherwise interval wording “engineering uncertainty band” hoga.
- Interval-width gate: `U-L ≤ max(0.10 mm, 0.15T)`; wider result abstains.
- Store full component budget, distribution source, covariance version, seed and interval; UI simplified value dikhaye.

## 12.3 Critical adversarial point

Low reprojection error planarity prove nahi karta. Unknown carton bow model error hai. Frame/flat-backing protocol + visual gate fail ho to abstain.

## 12.4 Test

Empirical interval coverage, repeatability SD, bias, P95 absolute error, selective risk vs abstention, and device/operator strata report kiye jayenge.

---

# 13. Abstention and state machine

## 13.1 Measurement state machine

```text
NOT_REQUESTED
 → FRAME_REQUIRED
 → CAMERA_CAL_VALID / PHYSICAL_SIZE_NOT_ESTABLISHED_CALIBRATION
 → FIDUCIAL_VALID / ..._FIDUCIAL
 → IMAGE_QUALITY_VALID / ..._IMAGE_QUALITY
 → GEOMETRY_VALID / ..._GEOMETRY
 → PLANARITY_ACCEPTED / ..._NON_PLANAR
 → GLYPH_ASSIGNMENT_VALID / ..._SEGMENTATION
 → UNCERTAINTY_ACCEPTABLE / ..._UNCERTAINTY
 → MEETS_SCREENING_THRESHOLD
   | POTENTIAL_UNDERSIZE
   | REQUIRES_OFFICER_REVIEW_BORDERLINE
```

Every new capture invalidates previous derived measurement unless explicitly retained as a separate run. Failed state old pass/fail ko display nahi karega.

## 13.2 Inspection result semantics

1. **INSUFFICIENT_EVIDENCE:** required face unavailable/unreadable, critical applicability fact unknown, or source evidence missing. “Not found” cannot become “absent.”
2. **PHYSICAL_SIZE_NOT_ESTABLISHED:** only physical-size branch failed; reason recorded. Other declaration findings may still exist.
3. **REQUIRES_OFFICER_REVIEW:** OCR ambiguity, borderline interval, contradiction, unresolved applicability/precedence, or unsupported field semantics.
4. **POTENTIAL_NON_COMPLIANCE:** complete relevant evidence plus deterministic candidate failure, such as verified field absence after full coverage or measurement upper bound below verified threshold. Still not legal verdict.
5. **COMPLIANT_SCREENING:** all in-scope machine-checkable checks satisfied, required coverage complete, no blocking unknown/contradiction, and officer reviewed. Means only “screening checks did not identify an issue.”

## 13.3 Deterministic aggregation and precedence

Per-rule outcomes, measurement and contradictions **coexist**; one package status detail findings ko erase nahi karta. Reducer order:

1. Critical applicability/date/source missing → overall `INSUFFICIENT_EVIDENCE`; any independent `POTENTIAL_NON_COMPLIANCE` finding remains visible but package cannot be cleared.
2. No critical gap, but required physical-size branch failed → `PHYSICAL_SIZE_NOT_ESTABLISHED`; unrelated candidate findings remain visible.
3. Unresolved blocking contradiction, OCR ambiguity or interval overlap → `REQUIRES_OFFICER_REVIEW`.
4. At least one conclusive candidate failure and no higher blocker → `POTENTIAL_NON_COMPLIANCE`.
5. All required in-scope rules `SATISFIED/NOT_APPLICABLE`, readable coverage complete, no blocking unknown/conflict, and officer reviewed → internal `COMPLIANT_SCREENING`.

UI/PDF mein `COMPLIANT_SCREENING` ka visible label **“NO ISSUE IDENTIFIED IN COMPLETED IN-SCOPE SCREENING CHECKS”** hoga; “compliant certificate” wording forbidden. Reducer inputs and output reason list report mein persisted honge.

Officer correction full re-evaluation trigger karega. Officer override machine finding mutate nahi karta; append-only disposition/reason add karta hai.

---

# 14. Multi-face contradiction architecture

## 14.1 Coverage model

For rectangular carton, required slots are `FRONT`, `BACK`, `LEFT`, `RIGHT`, `TOP`, `BOTTOM`. `OVERLAY` records sticker/overprint separately with `covers_capture_id` and polygon.

**Important correction to prior blueprint:** capture accounting declaration presence se calculate nahi hoga. Otherwise missing field prove karna circular ho jata hai. Do alag values maintain hongi:

- `surface_accounting_complete`: every required slot captured, explicitly inaccessible, or legitimately not applicable.
- `readable_evidence_complete`: every required slot has adequate readable evidence.

`NOT_ACCESSIBLE` first value complete kar sakta hai, second ko kabhi complete nahi karta; therefore absence finding block rahegi. Declaration completeness sirf readable evidence complete hone ke baad evaluate hoti hai.

## 14.2 Observation graph

```text
Package
 ├─ Face slot
 │   ├─ Original capture
 │   ├─ OCR spans
 │   └─ Declaration observations
 └─ Overlay/sticker
     ├─ covers base region
     └─ independent observations
```

Each observation has typed field, normalized value, raw span, scope, face, layer, confidence and review status.

## 14.3 Contradiction rules

- MRP: exact decimal/currency mismatch → contradiction; sticker may be permitted in some cases, but engine does not auto-resolve legality.
- Net quantity: unit-normalized physical dimension mismatch → contradiction.
- Date: compare only same semantic type; manufacture vs expiry is not conflict.
- Country of origin: incompatible normalized countries → contradiction.
- Entity/address: fuzzy mismatch creates review candidate, not automatic contradiction.
- OCR alternatives: if confidence insufficient, status `AMBIGUOUS`, not contradiction.

`contradiction` retains all members, comparator version, status and officer resolution. “Latest face”, “sticker wins” or “highest OCR confidence wins” forbidden.

## 14.4 Test

Seed exact duplicates, unit-equivalent values (`1 kg` vs `1000 g`), real mismatches, semantic date differences, uncertain OCR and sticker overlays. Measure precision/recall and verify both source cards remain visible.

---

# 15. Legal rule-engine schema

## 15.1 Rule record — exact JSON contract

```json
{
  "rule_id": "PCR2011-R6-DECL-MRP",
  "version": 3,
  "schema_version": 1,
  "title": "MRP declaration screening",
  "citation": {
    "instrument": "Legal Metrology (Packaged Commodities) Rules, 2011",
    "locator": "REQUIRES_VERIFIED_CURRENT_LOCATOR",
    "source_uri": "official-source-uri",
    "source_sha256": "64-hex",
    "gazette_number": null,
    "publication_date": "YYYY-MM-DD"
  },
  "valid_from": "YYYY-MM-DD",
  "valid_to_exclusive": null,
  "date_basis": "INSPECTION_DATE",
  "knowledge_from": "YYYY-MM-DDTHH:mm:ssZ",
  "knowledge_to_exclusive": null,
  "legal_status": "VERIFIED_RULE",
  "applicability": {
    "op": "all",
    "args": [
      {"op": "eq", "fact": "inspection.mode", "value": "PHYSICAL_RETAIL"},
      {"op": "eq", "fact": "package.in_scope", "value": true}
    ]
  },
  "exceptions": [],
  "requirement": {
    "type": "DECLARATION_PRESENT",
    "field": "MRP",
    "parameters": {}
  },
  "evidence_required": [
    {"type": "FACE_COVERAGE", "minimum": "ALL_REQUIRED_READABLE"},
    {"type": "DECLARATION_OBSERVATION", "field": "MRP"}
  ],
  "machine_checkable": "PARTIAL",
  "policy_priority": "NORMAL",
  "human_review": "MANDATORY_BEFORE_REPORT",
  "supersedes": "PCR2011-R6-DECL-MRP@2",
  "precedence_edges": [],
  "unknown_behavior": "INDETERMINATE",
  "test_fixture_ids": ["FIX-R6-MRP-001"],
  "content_hash": "64-hex",
  "review": {
    "mapped_by": "rules-admin-id",
    "legal_reviewed_by": "second-reviewer-id",
    "approved_at": "YYYY-MM-DDTHH:mm:ssZ"
  }
}
```

## 15.2 Closed predicate grammar

Allowed ops: `all`, `any`, `not`, `eq`, `neq`, `in`, `exists`, typed numeric compare, `date_between`, bounded collection predicates and explicit definition lookup. Arbitrary JavaScript/Python/SQL, network calls, runtime prompts and unrestricted regex forbidden.

Evaluation outputs per rule:

```text
SATISFIED | NOT_SATISFIED | INDETERMINATE | NOT_APPLICABLE
```

Each output includes consumed facts/evidence, trace, rule hash and reason code.

## 15.3 Why needed / fail / test

- **Needed:** static checklist amendment ke baad silently wrong ho sakta hai.
- **Evidence:** 2025–2026 amendments date/category/supply-chain routing change dikhate hain.
- **Fail:** wrong commencement date, overlapping versions, incorrect exception precedence, mutable URL.
- **Test:** golden fixtures at date boundaries, unknown facts, category routing, conflict, supersession and old-report replay.

---

# 16. Rule version and effective-date logic

Use bitemporal concepts:

- `valid_from/valid_to_exclusive`: law real-world mein kab applies.
- `knowledge_from/knowledge_to_exclusive`: system ne mapping kab publish/know ki.

Selection inputs:

```text
legal_event_dates = {
  inspection_date,
  offer_for_sale_date?,
  manufacture_date?,
  packing_date?,
  import_date?,
  warehouse_exit_date?
}
knowledge_as_of = active signed rule-pack cutoff
jurisdiction = explicit
facts = typed applicability observations with source/status
```

Har rule version `date_basis` declare karega; engine generic “latest date” choose nahi karega. Missing required event date → `INDETERMINATE_EVENT_DATE`. MVP rules default inspection date tabhi use karenge jab reviewed mapping explicitly usko correct date basis mark kare.

Algorithm:

1. Signed pack and hashes verify.
2. Rule-declared `date_basis` se selected event date par candidate versions choose karo: `valid_from <= selected_date < valid_to`; knowledge interval bhi match hona chahiye.
3. Applicability three-valued logic: TRUE/FALSE/UNKNOWN.
4. Explicit reviewed exception/precedence edges apply; “specific always wins” hard-code nahi.
5. Multiple unresolved applicable versions/conflict → `INDETERMINATE_RULE_CONFLICT`.
6. Missing commencement/effective date → `INDETERMINATE_EFFECTIVE_DATE`.
7. Evaluation stores exact pack/rule/content hash. Historical pack retained.

Device clock authoritative nahi. Inspection date user-entered legal fact hai; capture chronology device time + last trusted server time basis ke saath store hoti hai.

## Signed rule-pack publication lock

- Canonical JSON: RFC 8785-style deterministic canonicalization; UTF-8 NFC strings; decimals as canonical strings; dates ISO-8601.
- Manifest includes every rule/source hash, schema/engine compatibility, jurisdiction, knowledge cutoff, creation time, signer key ID and previous-pack hash.
- Signature: Ed25519 over manifest hash; trusted public keys pinned in app.
- Activation validates signature, source/rule closure, interval overlap, precedence cycles, AST depth/node limits, fixture pass and minimum app/engine version.
- Rotation: old/new signer overlap pack; revocation list cached with issue/expiry. Offline expired revocation data allows old assigned-case replay but blocks new rule-pack activation/export warning-free.
- Anti-rollback: highest accepted monotonic pack sequence stored in hardware-backed state; rollback only through separately signed emergency rollback record.
- Staged download + atomic pointer switch; crash leaves previous pack active.
- Historical pack/engine compatibility retained for report replay; missing interpreter returns `PARTIAL_MISSING_RUNTIME`, never silently reevaluates with a newer engine.

## Legal mappings requiring source re-verification before code/PPT

1. Current Rule 7 character-height/width table and exact measurand wording.
2. Rule 8 PDP geometry/area formula for rectangular cartons.
3. Which declaration and glyph classes each threshold applies to.
4. Rule 27 vs Rule 33 references in prior blueprint; registration, permissions and quantity references must be corrected.
5. Current consolidated Rule 6 wording for MRP, date, consumer care, origin and unit sale price.
6. Rule 3 scope/exclusions and package quantity/consumer facts.
7. Sticker/overprint and price alteration treatment.
8. Medical-device routing effective 24 Oct 2025.
9. Pan-masala Rule 26(a) routing effective 1 Feb 2026.
10. E-commerce Rule 6(10A) 1 Jul 2026/1 Jul 2027 interaction—future, not MVP.
11. AEO warehouse stage and Rule 27 changes effective 29 May 2026—future routing.
12. Any historical amendment omitted from supplied consolidated evidence.

Until 1–5 are verified, demo threshold is labelled **configured engineering test threshold**, not statutory conclusion.

---

# 17. Evidence model

## 17.1 Evidence principles

- Original bytes immutable.
- Crop, rectification, enhancement, OCR and report are derivatives with lineage.
- Hash proves byte consistency after capture, not truth/authenticity.
- Device timestamp/GPS are metadata claims, not infallible facts.
- Every machine finding must trace to evidence and rule.
- Every correction/override is append-only.

## 17.2 Required entities

| Entity | Critical fields |
|---|---|
| `inspection` | id, officer/device, legal date, location, status, rule_pack_id, calibration profile |
| `package` | archetype, SKU/batch, category facts, import/scope facts, measured dimensions source |
| `face` | slot, coverage state, PDP assertion, reason |
| `capture` | original artifact, face, layer, timestamp/time basis, device settings, quality results |
| `ocr_span` | polygon, raw text, alternatives, confidence, model/version, capture |
| `declaration` | typed field, raw/normalized value, unit, source span, review state |
| `measurement` | frame/camera IDs, glyph policy, h/L/U, budget, gates, algorithm version |
| `rule_evaluation` | rule/version/hash, inputs, trace, result, reason |
| `evidence_artifact` | hash, media type, size, storage key, derivative lineage, transform |
| `contradiction` | predicate, member observations, comparator, state, resolution |
| `officer_review` | target, action, reason, before/after, actor/time |
| `report` | version, manifest hash, source IDs, rule pack, supersedes, signatures |
| `audit_event` | actor/device, entity/action, payload hash, previous hash, signature |

Evidence status vocabulary:

```text
OBSERVED | MACHINE_EXTRACTED | OFFICER_CONFIRMED | DISPUTED |
UNREADABLE | NOT_CAPTURED | UNKNOWN | DERIVED | VERIFIED_RULE
```

`VERIFIED_FACT` wording only instrument-backed/directly confirmed contexts mein use hoga; raw OCR ko verified fact label nahi karna.

---

# 18. Offline-first architecture

## 18.1 Component layout

```text
Android client (offline trust boundary)
 ├─ Capture/CV/OCR
 ├─ Deterministic parser + rule evaluator
 ├─ Measurement engine
 ├─ Review/report UI
 ├─ SQLCipher database
 ├─ Encrypted content-addressed blob store
 ├─ Signed local rule packs
 └─ Outbox/inbox sync worker

Optional server
 ├─ FastAPI sync/auth API
 ├─ PostgreSQL metadata/event store
 ├─ S3/MinIO encrypted blobs
 ├─ Signed rule-pack publisher
 └─ React supervisor dashboard
```

## 18.2 Fully offline

Inspection create/edit, capture, OCR, extraction, rule evaluation, measurement, contradiction detection, officer review, local report, history and queue creation.

## 18.3 Online optional

Login/grant refresh, encrypted sync, rule-pack download, backup, supervisor dashboard and central report verification.

## 18.4 Human-gated only

Officer-reviewed report finalisation/export; correction/override; unresolved contradiction disposition; manual category/PDP/applicability assertion.

### Failure containment
No connectivity core result ko block nahi karegi. Expired offline authorisation par policy can allow assigned-case view/edit but block export/share/admin; production policy DoCA se confirm hogi.

---

# 19. Sync model

Use transactional **outbox + canonical server events**, not whole-database sync and not last-write-wins.

1. Local command same transaction mein projection update, audit event and outbox operation create karta hai.
2. `operation_id` client-generated and idempotent.
3. Upload includes expected aggregate version, payload hash, device signature.
4. Blob first resumably uploads/finalizes; dependent metadata then accepted.
5. Server validates auth/schema/version/hash; assigns canonical event/cursor.
6. Version conflict local work delete nahi karta; `sync_conflict` queue.
7. Auto-merge only commutative append operations. Same field edit, review, deletion, legal date or resolution needs human merge.
8. Inbound events strictly cursor order; gap par aggregate snapshot, skip nahi.
9. Rule packs separate signed pull-only channel; stage → validate → atomic activate; partial pack forbidden.
10. Reports immutable; new version supersedes old.

### Offline conflict tests
Network cut during blob, duplicate retry, app crash after local commit, out-of-order events, same declaration edited on two devices, revoked device reconnect, stale rule pack and storage exhaustion.

---

# 20. Database schema

SQLite/Room local schema; server mirrors domain entities in PostgreSQL. IDs UUIDv7/ULID; money integer minor units; measurements decimal strings/fixed-point—not binary float in persisted comparisons.

```text
inspection(
  id PK, officer_id, device_id, legal_date, jurisdiction,
  status, rule_pack_id, calibration_profile_id,
  created_at, updated_at, aggregate_version)

package(
  id PK, inspection_id FK UNIQUE, archetype, sku, batch,
  category_code, retail_wholesale, import_status,
  quantity_value_decimal, quantity_unit, applicability_facts_json)

face(
  id PK, package_id FK, slot, coverage_state, is_candidate_pdp,
  officer_reason, UNIQUE(package_id, slot))

artifact(
  id PK, inspection_id FK, kind, status, created_at)

artifact_version(
  id PK, artifact_id FK, version_no, plaintext_sha256,
  ciphertext_sha256, byte_size, media_type, storage_key,
  derived_from_id FK NULL, transform_json, captured_at,
  time_basis, UNIQUE(artifact_id, version_no))

capture(
  id PK, face_id FK, artifact_version_id FK, layer,
  covers_capture_id FK NULL, device_settings_json,
  gps_json NULL, quality_json, capture_state)

ocr_span(
  id PK, capture_id FK, polygon_json, raw_text,
  alternatives_json, confidence_decimal, script,
  model_id, model_version, preprocessing_json)

declaration_observation(
  id PK, package_id FK, field_type, semantic_subtype,
  raw_value, normalized_value_json, unit, ocr_span_id FK NULL,
  source_type, confidence_basis, review_state, created_by)

contradiction(
  id PK, package_id FK, predicate_key, comparator_version,
  status, severity, resolution_id FK NULL, created_at)

contradiction_member(
  contradiction_id FK, declaration_id FK, value_hash, role,
  PRIMARY KEY(contradiction_id, declaration_id))

measurement_run(
  id PK, capture_id FK, rule_evaluation_id FK NULL,
  frame_id, camera_calibration_id, algorithm_version,
  measurand_policy_id, threshold_decimal NULL,
  estimate_decimal NULL, lower_decimal NULL, upper_decimal NULL,
  uncertainty_json, gates_json, status, reason_code)

measurement_glyph(
  id PK, measurement_run_id FK, glyph_label, polygon_json,
  estimate_decimal, lower_decimal, upper_decimal,
  segmentation_json, eligible_boolean)

rule_pack(
  id PK, version, manifest_hash, signer_key_id, signature,
  knowledge_cutoff, status)

rule_version(
  id PK, pack_id FK, stable_rule_id, version,
  valid_from, valid_to_exclusive, knowledge_from,
  knowledge_to_exclusive, citation_json, applicability_json,
  exceptions_json, requirement_json, evidence_required_json,
  machine_checkable, human_review, content_hash)

rule_evaluation(
  id PK, inspection_id FK, rule_version_id FK,
  engine_version, input_manifest_hash, result,
  reason_code, trace_json, evaluated_at)

officer_review(
  id PK, inspection_id FK, target_type, target_id,
  action, reason_code, comment, prior_hash, resulting_hash,
  officer_id, reviewed_at)

report(
  id PK, inspection_id FK, version, canonical_json_artifact_id FK,
  pdf_artifact_id FK, manifest_hash, status,
  supersedes_report_id FK NULL, created_at)

audit_event(
  id PK, inspection_id FK NULL, device_id, actor_id,
  event_type, entity_type, entity_id, occurred_at,
  recorded_at, payload_hash, previous_device_hash,
  event_hash, signature)

outbox(
  operation_id PK, aggregate_type, aggregate_id,
  expected_version, operation_type, payload_json,
  payload_hash, dependencies_json, state,
  attempt_count, next_attempt_at, last_error_code)

inbox_event(
  server_event_id PK, cursor UNIQUE, aggregate_type,
  aggregate_id, aggregate_version, event_type,
  payload_json, payload_hash, applied_at)

sync_conflict(
  id PK, operation_id FK, expected_version, actual_version,
  server_snapshot_json, status, created_at)
```

Required indexes: inspection date/status; face package/slot; OCR capture; declaration package/type; artifact hash; rule stable ID/date interval; evaluation inspection; outbox state/next attempt.

## 20.1 Immutability and omitted-core tables

`applicability_facts_json` convenience projection hai, source of truth nahi. Every legal fact append-only entity hoga:

```text
fact_observation(
  id PK, inspection_id FK, fact_key, typed_value_json,
  source_artifact_id FK NULL, source_kind, evidence_status,
  valid_from NULL, valid_to NULL, supersedes_id FK NULL,
  created_by, created_at, content_hash)

contradiction_resolution(
  id PK, contradiction_id FK, resolution_type, chosen_member_id NULL,
  rationale, supporting_artifact_id FK NULL, officer_id, created_at)

calibration_frame(
  id PK, serial UNIQUE, coordinate_manifest_hash,
  certificate_artifact_id FK, uncertainty_json, flatness_decimal,
  issued_at, expires_at, status)

camera_calibration(
  id PK, device_model, camera_id, resolution, focus_zoom_profile,
  intrinsics_json, covariance_json, residuals_json,
  certificate_artifact_id FK, issued_at, expires_at, status)

calibration_control_run(
  id PK, camera_calibration_id FK, frame_id FK, coupon_id,
  expected_json, observed_json, result, artifact_id FK, run_at)

identity(id PK, tenant_id, role, public_key, status)
device(id PK, identity_id FK, public_key, attestation_state, status)
offline_grant(id PK, identity_id FK, device_id FK, scope_json,
              issued_at, expires_at, revoked_at NULL, signature)
key_envelope(id PK, inspection_id FK, recipient_type, recipient_id,
             algorithm, wrapped_dek, key_version, created_at, revoked_at NULL)
rule_review(id PK, rule_version_id FK, reviewer_id, action, comment,
            source_hash, created_at, signature)
```

Corrections `supersedes_id` se new row create karengi; old declaration/fact update nahi. Mutable workflow projection tables allowed hain, but evidence/fact/measurement/evaluation/review/report rows par DB triggers `UPDATE/DELETE` reject karenge except retention-authorised tombstone transaction. Audit event mein per-device sequence and genesis ID mandatory. Schema migrations signed/checksummed honge; migration ke baad historical report replay fixture pass required.

`rule_version` physical table §15 ke complete contract ko store karega, including legal status, priority, precedence edges, unknown behavior, fixtures and approval links; abbreviated listing implementation ko fields drop karne ki permission nahi deta.

---

# 21. API architecture

## 21.1 Local APIs/modules

```text
CaptureService
OcrService
DeclarationParser
MeasurementService
RuleEvaluator
ContradictionService
EvidenceRepository
ReviewService
ReportService
SyncCoordinator
```

Interfaces typed and deterministic; UI directly model internals access nahi karega.

## 21.2 Optional server REST

```text
POST /api/v1/auth/device/register
POST /api/v1/sync/operations:batch
GET  /api/v1/sync/events?after={cursor}
GET  /api/v1/aggregates/{type}/{id}/snapshot
POST /api/v1/blobs:initiate
PUT  /api/v1/blobs/{id}/chunks/{n}
POST /api/v1/blobs/{id}:finalize
GET  /api/v1/rule-packs/latest?jurisdiction=...
GET  /api/v1/rule-packs/{id}/manifest
GET  /api/v1/rule-packs/{id}/content
POST /api/v1/reports:verify
```

Minimal sync command envelope:

```json
{
  "device_id": "uuid",
  "after_cursor": 1842,
  "operations": [{
    "operation_id": "uuidv7",
    "aggregate_type": "inspection",
    "aggregate_id": "uuidv7",
    "expected_version": 7,
    "type": "ADD_DECLARATION_OBSERVATION",
    "payload": {},
    "payload_sha256": "64-hex",
    "dependencies": ["blob-version-id"],
    "device_signature": "base64"
  }]
}
```

Response per operation: `ACCEPTED | CONFLICT | REJECTED`, canonical aggregate version/event ID, retryable flag and stable error code. Idempotency record minimum retention prototype mein 90 days; cursor compaction se pehle signed aggregate snapshots retained. Chunk finalization verifies per-chunk and whole-ciphertext hash, size and envelope existence. Retry ceiling ke baad operation `REJECTED/CONFLICT` queue mein human-visible rahega; data silently drop nahi hoga.

`reports:verify` bytes/provenance/recomputation verify karta hai; legal correctness certify nahi.

Every mutation: `operation_id`, `expected_version`, auth scope and stable error code. Raw evidence/log content diagnostics mein leak nahi hoga.

## 21.3 Chosen server stack

FastAPI + Pydantic, PostgreSQL, S3-compatible MinIO/object storage, background worker, React/TypeScript dashboard. Server MVP optional; local demo ko server dependency nahi.

---

# 22. Security and integrity model

1. SQLCipher database encryption; DB key Android Keystore-backed.
2. Evidence blobs AES-GCM encrypted; per-inspection data key wrapped by device key.
3. TLS and short-lived scoped tokens online.
4. Original evidence immutable; derivatives linked by hash and transform metadata.
5. SHA-256 plaintext/ciphertext hashes; storage keys opaque/HMAC-derived.
6. Audit events per-device hash-chain + device signature; sync par server anchor.
7. Signed rule packs with pinned publisher key, key ID, rotation/revocation and anti-rollback check.
8. Role and inspection-level authorization server-side; offline cached grant expiry explicit.
9. PDF not source of truth; canonical JSON + manifest source of truth.
10. Export action logged; sensitive logs redacted; screenshots/backups policy-controlled.
11. Imported files hostile input: MIME/size/decompression limits and quarantine.
12. No claim of “tamper-proof” or evidence authenticity. Hash-chain detects many post-capture modifications after anchoring; compromised authorised device can still fabricate capture.

### Integrity verification statuses

```text
VERIFIED_BYTES
VERIFIED_RECOMPUTATION
PARTIAL_MISSING_INPUTS
FAILED_INTEGRITY
```

Officer signature in prototype is local attestation/device signature, not assumed statutory digital signature.

## 22.1 Key lifecycle and trust boundary

- Each inspection has random AES-256-GCM DEK; every blob uses unique 96-bit nonce and AAD `(tenant, inspection, artifact, version, media_type)`.
- DEK is wrapped to current device hardware key. Once synced, same DEK is additionally wrapped to tenant recovery/KMS key; authorised second device/supervisor gets a fresh recipient-specific envelope after server grant check.
- Server/KMS is an explicit trusted decryption boundary for supervisor dashboard. If deployment requires zero-knowledge storage, web preview is disabled and client-side decrypt required.
- Lost **unsynced** device evidence is unrecoverable by design; UI warns and encourages sync/export. Lost synced device can be revoked and DEK rewrapped to authorised replacement.
- Keystore invalidation, key rotation, revocation, backup restore and envelope migration have test fixtures. Key material/logs/backups never contain plaintext DEK.

## 22.2 Canonical report lock

Canonical JSON uses deterministic UTF-8 NFC serialization, canonical decimal strings, UTC timestamps plus explicit legal date/time-zone fields, sorted arrays where order is not semantic, and pinned schema version. Manifest signs path, media type, byte size and SHA-256 for canonical JSON, evidence derivatives and PDF. Renderer, template, font and model hashes are provenance fields; nondeterministic PDF metadata removed. Signature payload is manifest hash, not visual PDF alone. Superseding report keeps parent ID/hash and changed-input list. Historical runtime missing ho to verification `PARTIAL_MISSING_RUNTIME` return karega.

## 22.3 MVP privacy/records defaults

- Collect minimum officer ID, case metadata and optional GPS; GPS default off, explicit per-case enable, accuracy stored.
- No analytics/third-party crash upload in field build; local crash logs redact OCR text, paths, tokens and coordinates.
- Android screenshot/backup disabled for evidence screens/files by default.
- Export only officer-confirmed report package; recipient/reason logged.
- Prototype retention: user cannot hard-delete finalised inspection; can mark `PENDING_RETENTION_REVIEW`. Production retention, legal hold and erasure periods remain department policy and must be configured before deployment.
- Security incident path: revoke device/grant/signer, freeze sync, preserve audit anchor, issue signed rule-pack withdrawal, and document affected report IDs.

---

# 23. Validation dataset and metrics

## 23.1 Dataset lock

### A. Physical measurement benchmark

- **Development/tuning:** 120 unique printed planar coupons/carton panels.
- **Sealed test:** 450 independent physical panels from held-out print sheets/lots: 150 truly below `T`, 150 near threshold (75 each side within `T ± 10%`), 150 clearly above.
- Primary statistical unit = physical panel, not image. Three recaptures per panel are clustered repeats; panel-level median and mixed-effects/cluster-bootstrap analysis use hogi.
- Balanced incomplete Latin-square allocation across 3 operators, 3 angles (0°, 20°, 35°) and 2 supported phones; full factorial falsely claim nahi hoga.
- At least 4 font families, 3 weight/contrast conditions, 2 stocks; Latin and Devanagari strata separately reported, with minimum 100 held-out panels in any script for which a headline claim is made.
- Stress negatives separate: minimum 25 each for blur, glare, partial fiducial, wrong frame, crease/bow, >0.10 mm plane offset, curved surface and unstable glyph topology.
- Ground truth: optical comparator/toolmaker microscope or calibrated metrology microscope implementing the same measurand. Reference expanded uncertainty ≤ one-third intended system uncertainty. If unavailable, no physical-accuracy claim.
- Sealed-set manifest, hashes and analysis script preregistered; one custodian withholds labels until model/policy freeze.

### B. OCR/field dataset

- 300 team-purchased/consented package-face captures, split by physical SKU and print lot; minimum 100 Latin, 100 Devanagari/mixed-script, 100 stress-condition faces.
- Held-out set mein same SKU/artwork instance train/development se leak nahi hoga.
- Annotate polygons, exact raw transcription, field type, normalized value and review status; double-annotate 20% and report agreement.
- Freeze OCR model hash, preprocessing, supported device, peak RAM, median/P95 latency, licensing record and confidence-calibration mapping before sealed evaluation.

### C. Multi-face/contradiction set

- 180 package cases × six slots: 60 true typed contradictions, 60 unit-equivalent/corroborating duplicates, 60 no-conflict controls.
- Additional 30 incomplete/unreadable-face runs verify that system never promotes “not detected” to package absence.
- Precision/recall ke saath 95% confidence intervals reported; no universal contradiction claim.

### D. Exact five demo cases

1. **Clean complete carton:** all faces, consistent declarations, measurable above threshold.
2. **Undersized controlled print:** upper uncertainty bound below configured threshold.
3. **Missing declaration with incomplete first pass:** first result `INSUFFICIENT_EVIDENCE`; after final face, missing candidate may appear.
4. **MRP sticker contradiction:** printed and sticker MRP both retained; `REQUIRES_OFFICER_REVIEW`.
5. **Bad geometry/glare:** OCR may extract, measurement returns `PHYSICAL_SIZE_NOT_ESTABLISHED` with reason.

## 23.2 Metrics and acceptance targets

All numbers below **engineering targets hain, achieved results nahi**.

| Metric | Target before PPT claim | Notes |
|---|---:|---|
| Measurement signed bias | absolute ≤0.10 mm | Controlled planar sealed test |
| Measurement MAE | ≤0.15 mm | Report by device/angle/stock |
| P95 absolute error | ≤0.30 mm | No hidden abstained cases |
| Repeatability SD | ≤0.10 mm | Same panel, independent recapture |
| Empirical interval coverage | nominal 95%; exact/cluster-bootstrap 95% CI must include 95% and lower bound ≥90% | Report mean width |
| Threshold accuracy among conclusive | ≥90%, with 95% CI | Near-threshold separately |
| False-clear rate | zero observed among ≥150 independent undersized panels; one-sided 95% upper bound ≤2% | Undersized classified meet |
| False-accusation rate | point target ≤5%, 95% CI reported | Compliant classified potential failure |
| Unsafe-condition acceptance | ≤2% across each preregistered stress class | Complements abstention precision |
| Abstention precision | ≥90%, 95% CI reported | Abstained cases meet predefined unsafe gates |
| Controlled-condition abstention rate | ≤25% | Report selective risk + coverage |
| OCR CER clean/mixed-script | ≤5% / ≤10%, 95% cluster-bootstrap CI | Per script, SKU-held-out |
| Field extraction F1 | ≥0.90 clean controlled set, CI reported | Exact field matching |
| Contradiction precision/recall | point ≥0.90 each; 95% CI reported | Typed held-out cases |
| Missing-face warning recall | 100% in scripted slot protocol | Deterministic, not CV claim |
| Evidence trace completeness | 100% tested findings | Source + rule + engine + review links |
| Offline core completion | 100% five demo cases | Airplane mode |

A target miss means wording/scope downgrade, not metric concealment. Accuracy denominator mein abstentions separately report honge.

---

# 24. 90-second SIH demo

**Demo mode:** phone airplane mode; rehearsed controlled carton and real app. No prerecorded fake result. If capture time risky ho, inspection with genuine pre-captured faces open karna acceptable hai, but narrator clearly says “pre-captured test case.”

| Time | Action | Screen/evidence | Message |
|---:|---|---|---|
| 0–8 s | Airplane mode + case open | “Offline”, rule pack/date/calibration green chips | Core network-independent |
| 8–20 s | Guided faces | Six slots; one deliberately incomplete moment | Not-found ≠ absent |
| 20–30 s | Complete final face / OCR | MRP, quantity, date crops linked | OCR is evidence locator, not hero |
| 30–52 s | **Hero measurement** | Original with four-marker frame → rectified overlay → `2.72 mm`, interval `[2.58,2.86]`, configured `T=3.00 mm` → `POTENTIAL_UNDERSIZE` | Physical mm, uncertainty, guard band |
| 52–64 s | Bad capture toggle/case | Glare/geometry failure → `PHYSICAL_SIZE_NOT_ESTABLISHED` | System refuses false precision |
| 64–75 s | Contradiction | Printed MRP ₹120 vs sticker ₹125, two source crops | Conflict retained, not auto-resolved |
| 75–84 s | Officer review | Accept/escalate with reason; machine finding unchanged | Officer decides |
| 84–90 s | Report | PDF/JSON manifest, rule version, hashes, offline saved | End-to-end traceability |

**Hero number rule:** Final demo values actual validated case se aayenge; above numbers script placeholders hain and PPT result nahi.

Demo fallback:
- OCR failure: officer-corrected span path show; do not inject hidden result.
- Measurement gate fail: abstention itself valid demo; backup validated capture available.
- PDF slow: open already generated report version and show manifest.

---

# 25. Exact claims safe for PPT

## Safe now as design statements

- “Inspectra is designed as an offline-first Legal Metrology screening assistant for field officers.”
- “The architecture separates captured observation, machine screening and officer determination.”
- “The MVP targets controlled planar printed cartons; curved and moulded measurement is out of scope.”
- “Rule evaluations are designed to retain source citation, effective interval and exact rule-pack version.”
- “The system is designed to return explicit insufficient-evidence and physical-size-not-established states instead of forcing a verdict.”
- “Net quantity declaration screening is separate from physical quantity verification.”

## Safe only after corresponding proof gates pass

- “On our controlled planar test set, the prototype estimated printed glyph extent with **[measured MAE]** and **[measured interval coverage]**; test protocol and abstention rate are reported.”
- “The complete capture-to-report workflow ran in airplane mode on **[tested devices]**.”
- “Every tested finding traced to an original image region, OCR/measurement record, exact rule version and officer action.”
- “In our seeded multi-face test set, the prototype detected **[measured precision/recall]** contradictions while preserving both source values.”
- “When calibration, planarity or image quality gates failed, the prototype returned `PHYSICAL_SIZE_NOT_ESTABLISHED` in **[measured gate-test result]** cases.”

## Safe technical contrast wording

> “Single-image OCR by itself physical millimetres, unseen-face completeness, or dated rule applicability establish nahi karta; Inspectra in gaps ko explicit measurement, coverage and rule records se address karne ke liye designed hai.”

Ye technical limitation statement hai, universal competitor superiority claim nahi.

---

# 26. Claims that must NOT be made

- “First”, “only”, “unique”, “best”, “most advanced”, “different from every SIH team”.
- “Legal-grade measurement”, “court admissible”, “legally defensible/irrefutable” without formal validation and legal acceptance.
- “100% accurate/compliant”, “zero false positives”, “guaranteed violation detection”.
- “Tamper-proof”, “immutable evidence”, “authentic photograph guaranteed”.
- “AI decides compliance/non-compliance.”
- “Works on every package, bottle, pouch, curved surface or moulded text.”
- “Measures actual net quantity from image.”
- “Missing declaration” when required face coverage/readability incomplete.
- “Current law automatically updated” without signed reviewed ingestion workflow.
- “Integrated with Legal Metrology V2.0” without authorised integration.
- “Multilingual” without language/script-specific benchmark.
- “Offline” if OCR/rules/report silently need network.
- Any target metric as achieved result.
- Any Rule 27/33 mapping, threshold or date not reverified from controlling source.
- “Hash proves authenticity” or “device timestamp proves capture time.”

---

# 27. What must be technically proven before PPT

## Mandatory go/no-go gates

| Gate | Proof required | Binary pass condition | Failure action |
|---|---|---|---|
| G0 Enabled legal corpus | Every enabled MVP rule—not only Rule 7/8—has official source bytes/hash, verified locator, date basis/interval, applicability, exceptions, dual review and fixtures | 100% enabled rules satisfy corpus validator; unresolved rules disabled | Use configured engineering checks only; no legal citation finding |
| G1 Fiducial calibration | Serialized frame survey, camera profile, ≤0.10 mm plane/flatness control | All §10.3 gates and same-day coupon pass | Measurement feature disabled |
| G2 Pixel-to-mm accuracy | Preregistered sealed planar benchmark | §23 bias/MAE/P95 limits all met in claimed strata | No physical-accuracy claim; estimate labelled experimental |
| G3 Uncertainty validity | Empirical interval analysis | Coverage CI rule and max-width gate pass | No threshold decision; estimate/band only |
| G4 Abstention safety | Preregistered negative/stress set | Unsafe acceptance and abstention targets pass; stale result test zero failures | USP fails; redesign fixture/gates |
| G5 Contradiction | Held-out typed face/sticker set | §23 point targets met with CIs reported; both values preserved in 100% cases | Remove automated contradiction claim |
| G6 Evidence trace | Random sample plus automated provenance validator | 100% findings source/hash → observation → rule → review → report; no orphan | No evidence-linked claim |
| G7 Temporal rules | Date-basis/boundary/conflict/replay fixtures | 100% golden fixtures; unresolved case always indeterminate | Static checklist only; no versioned claim |
| G8 Offline core | Airplane-mode five cases on supported devices | 100% capture/OCR/rules/measure/review/report completion | Remove offline-first claim |
| G9 Integrity/report | Byte mutation, canonicalization, supersession and historical replay | Every mutation detected; same inputs produce same canonical JSON/manifest; expected partial status on missing runtime | Say hashes recorded only; no reproducibility claim |
| G10 Demo reproducibility | 10 rehearsals | ≥9 complete under 90 s without hidden network/manual DB edits | Simplify demo/scope |
| G11 OCR/extraction | SKU-held-out OCR/field benchmark | Script-specific §23 CER/F1 targets and latency/RAM budget pass | Limit supported fields/scripts; mandatory manual entry |
| G12 Identity/key/sync security | Device loss, grant expiry/revocation, key rewrap, duplicate/out-of-order sync and restore drills | All expected deny/recovery outcomes; no plaintext key/log leakage | Keep single-device offline demo; remove backup/multi-device claims |
| G13 Officer usability | 3+ domain users/proxies perform capture, review and report tasks | 100% critical task completion; no user interprets clear-screen state as legal certificate; median run within documented bound | Redesign labels/workflow; no officer-ready claim |
| G14 Privacy/accessibility | Data-flow review, screenshot/backup/export tests, keyboard/contrast/text-size checks | No critical privacy leak; core workflow usable at target text size/contrast | Prototype/demo-only, not deployment claim |

### PPT release rule

Final PPT ka problem/architecture draft ban sakta hai, but **performance, USP, offline, evidence-integrity, officer-readiness aur security claims freeze nahi honge** until their corresponding G0–G14 gates pass. Minimum hero claim needs G0–G4, G6–G11. Gate failure binary `FAIL` hai; fallback wording table mein defined hai—“almost passed” metric ko achieved nahi dikhaya jayega.

---

# Implementation contract for coding agent

## Build order

### Phase 0 — proof spike
1. Fiducial frame schema and camera calibration tool.
2. Offline image import/capture.
3. Marker detection, undistortion, homography and source-point mm mapping.
4. One manually selected glyph region; measurement JSON + gate reasons.
5. 20-panel pilot to expose model error.

**Stop condition:** If repeatability/ground truth cannot support a useful interval, UI/backend build se pehle measurement claim downgrade.

### Phase 1 — evidence skeleton
1. SQLCipher schema and encrypted blob store.
2. Inspection/package/face/capture entities.
3. Hash/derivative lineage and audit events.
4. Six-slot guided capture and quality states.

### Phase 2 — extraction and contradiction
1. ONNX OCR integration.
2. Span storage and deterministic field grammar.
3. Correction UI.
4. Typed observation grouping and contradiction engine.

### Phase 3 — rules and state machine
1. Signed local pack parser/validator.
2. Closed AST evaluator and four-valued logic.
3. Date-boundary fixtures.
4. Inspection result derivation.

### Phase 4 — review/report
1. Finding evidence cards.
2. Mandatory officer actions/reasons.
3. Canonical report JSON, manifest and deterministic PDF.
4. Local history/search.

### Phase 5 — optional sync
1. Outbox/inbox and idempotent API.
2. Blob upload.
3. Rule-pack pull/atomic activation.
4. Conflict UI and minimal dashboard.

## Definition of done

A feature is `REAL PROTOTYPE` only if executable on target phone, backed by stored evidence, and covered by a reproducible fixture/test. Static UI with hard-coded result is `CONTROLLED SIMULATION` and must be labelled. Unimplemented concepts remain `ROADMAP`.

| Capability | SIH status |
|---|---|
| Planar calibrated measurement | REAL only after G1–G4; otherwise proof spike |
| OCR + typed extraction | REAL |
| Six-face guided capture | REAL |
| MRP/quantity contradiction | REAL |
| Versioned local rule pack | REAL with small verified corpus |
| Officer review/report | REAL |
| Offline history | REAL |
| Server sync/dashboard | CONTROLLED SIMULATION or optional real stretch |
| Curved/moulded measurement | ROADMAP + real abstention |
| Physical quantity verification | ROADMAP |
| E-commerce mode | ROADMAP |
| Government API integration | ROADMAP/UNKNOWN |
| Medical-device detailed checks | ROADMAP; route-only |

---

# Major decision audit matrix

| Decision | Why needed | Evidence basis | What can fail | How tested |
|---|---|---|---|---|
| Officer-first physical MVP | Highest problem fit | Problem statement + dossier workflow | Calibration overhead unusable | Officer/proxy task test |
| Planar-only | Homography assumes plane | CV geometry | Bow/crease/plane offset | Stress negatives + abstention |
| Four-marker enclosing frame | Redundant same-plane metric control | Metrology reasoning | Bad survey/warped frame | Control coupon, leave-one-marker test |
| Camera calibration | Homography alone lens distortion remove nahi karta | CV fundamentals | Setting mismatch | Held-out reprojection/control check |
| Direct source-contour mapping | Rectification resampling bias avoid | Measurement audit | Segmentation unstable | Threshold sensitivity/ground truth |
| Interval guard bands | Near threshold hard verdict unsafe | Uncertainty principle | Miscalibrated interval | Empirical coverage |
| Independent coverage/declaration completeness | Missing proof circularity avoid | Multi-face logic | Officer wrong slot marking | Incomplete-face scripted tests |
| Preserve contradictions | Sticker chronology/legal meaning uncertain | Evidence audit | False conflicts from OCR/unit | Typed comparators + review set |
| Closed deterministic rule AST | Reproducible and bounded | Amendment/rule provenance need | Bad legal mapping | Golden legal fixtures + dual review |
| Bitemporal rule data | Old inspection replay and late knowledge | Amendments/effective dates | Publication/commencement confusion | Boundary and replay tests |
| No LLM in MVP decision path | Determinism/offline/safety | Legal boundary | Parser recall lower | Field F1 + correction UI |
| Canonical JSON before PDF | PDF presentation artifact | Integrity/reproducibility | Renderer variance | Hash/recompute tests |
| Outbox sync/no LWW | Offline concurrent edits preserve | Evidence integrity | Conflict overload | Fault injection |
| Hash-chain with limited claim | Detect modifications, not truth | Security threat model | Device compromise/rewrite | Mutation + server anchor tests |
| ONNX OCR, no LLM decision | Offline reproducibility and span linkage | Master context legal boundary; deterministic replay need | Model/license/device mismatch | Model-hash, SKU-held-out CER/F1, latency/RAM gate |
| SQLCipher + encrypted blob store | Lost/stolen device exposure reduce | Field-device threat model | Keystore loss, WAL/temp leak | Device-loss, backup, forensic file checks |
| Envelope key lifecycle | Backup/multi-device access without one shared key | Sync and revocation requirements | Lost unsynced data, bad rewrap | G12 recovery/revocation drills |
| Signed atomic rule packs | Offline legal corpus cannot silently mutate | Effective-date and provenance requirement | Bad publisher key, rollback, partial activation | Signature/rotation/revocation/crash fixtures |
| Append-only fact/evidence rows | Correction history and replay preserve | Officer override/evidence requirement | Mutable projection mistaken as truth | DB update/delete rejection + replay |
| Canonical JSON + pinned report inputs | PDF alone reproducible source nahi | Audit/report trace requirement | Unicode/decimal/font drift | Golden manifest and cross-run hash test |
| Minimal GPS/privacy defaults | Evidence usefulness with data minimization | PII/location risk | OS backup/screenshot/log leakage | G14 data-flow and leakage tests |
| REST outbox API | Network loss and idempotent recovery | Offline-first requirement | duplicate, cursor gap, conflict flood | Fault-injection matrix |
| Signed migrations/historical runtimes | Old reports future app par replay hon | Temporal audit requirement | schema destroys semantics | Migration + old-pack replay fixtures |
| Manual face/PDP assertions | Full auto-classification unreliable in MVP | Scope and workflow evidence | Officer misclassification | Review UI + user task test |
| Result label qualification | Required status preserve but legal clearance avoid | Legal-safety principle | “compliant” misread | G13 comprehension test |

---

# Final definitive blueprint

**Build this and nothing broader until proof gates pass:**

A Kotlin Android application creates an inspection offline, records explicit applicability facts, guides a rectangular carton through six face slots, preserves encrypted originals and hashes, runs bundled OCR, creates typed declaration observations, detects MRP/quantity contradictions without resolving them, and uses a surveyed four-marker co-planar frame plus calibrated camera profile to estimate selected printed glyph extent in millimetres. The measurement engine emits component uncertainty and either a guard-band screening state or a specific abstention reason. A signed immutable rule pack selects reviewed rule versions by inspection date using three/four-valued deterministic logic. Every candidate finding links to source polygon, raw/normalized observation, exact rule hash, engine version and officer review. The app generates canonical JSON and PDF offline, stores immutable report versions locally, and optionally syncs through an idempotent outbox without last-write-wins.

**Product success is not “the app produced a violation.” Product success is “the app knew exactly what its evidence could and could not support, preserved that boundary, and made the result reproducible.”**
