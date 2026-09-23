# Graph Report - Inspectra  (2026-09-23)

## Corpus Check
- 153 files · ~171,717 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 36 file(s) not represented in the graph (top: .css 29, .csv 3, (none) 2)

## Summary
- 1312 nodes · 3145 edges · 51 communities (48 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 30 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Synthetic Rendering & Grid
- Reference Table Validation
- Glyph Glyph Selection
- Physical Analyzer Verification
- Setup Gate (B2 Setup Gate)
- Flatness Acceptance Check
- Inventory & Fixture Audit
- SIH Presentation Deck Builder
- Core Math & Primitives
- Physical Analyzer Verification
- Web UI & Dependencies
- Camera Model & Homography
- Camera Model & Homography
- Synthetic Rendering & Grid
- Measure Module
- Web UI & Dependencies
- Synthetic Rendering & Grid
- Verify B2 Setup Module
- Camera Model & Homography
- Validate Selection Module
- Synthetic Rendering & Grid
- Flatness Acceptance Check
- Synthetic Rendering & Grid
- Web UI & Dependencies
- Synthetic Rendering & Grid
- Manifest Module
- Web UI & Dependencies
- Reference Table Validation
- Web UI & Dependencies
- Camera Model & Homography
- Web UI & Dependencies
- Glyph Make Glyph Map
- Inventory & Fixture Audit
- Web UI & Dependencies
- Web UI & Dependencies
- Physical Analyzer Verification
- Core Math & Primitives
- Setup Gate (Gates)
- Web UI & Dependencies
- Camera Model & Homography
- Web UI & Dependencies
- Web UI & Dependencies
- Synthetic Rendering & Grid
- Fiducial Module
- Setup Gate (Gates)
- Make Coupons Svg Module
- Synthetic Rendering & Grid
- Web UI & Dependencies
- Experiments Module
- P0 Module
- Web UI & Dependencies

## God Nodes (most connected - your core abstractions)
1. `dump_json()` - 52 edges
2. `load_json()` - 50 edges
3. `glyph()` - 42 edges
4. `satisfied()` - 41 edges
5. `Camera` - 40 edges
6. `ref_row()` - 39 edges
7. `codes()` - 38 edges
8. `register()` - 33 edges
9. `run_for()` - 32 edges
10. `check()` - 32 edges

## Surprising Connections (you probably didn't know these)
- `measure_run()` --uses--> `Camera`  [INFERRED]
  phase0/p0/pipeline.py → phase0/p0/camera.py
- `process_frame()` --uses--> `Camera`  [INFERRED]
  phase0/p0/pipeline.py → phase0/p0/camera.py
- `render_burst()` --uses--> `Camera`  [INFERRED]
  phase0/p0/render.py → phase0/p0/camera.py
- `render_frame()` --uses--> `Camera`  [INFERRED]
  phase0/p0/render.py → phase0/p0/camera.py
- `TestMisplacedRoiAbstains` --uses--> `Camera`  [INFERRED]
  phase0/tests/test_glyph_roi_map.py → phase0/p0/camera.py

## Import Cycles
- None detected.

## Communities (51 total, 3 thin omitted)

### Community 0 - "Synthetic Rendering & Grid"
Cohesion: 0.08
Nodes (25): check(), codes(), filled_roi(), glyph(), manifest_for(), Tests for the pre-registered glyph / ROI map (blocker B3). These test…, Determinism: the map is derived, never hand-edited., Independent replay of `coupon()`'s own row/column arithmetic. (+17 more)

### Community 1 - "Reference Table Validation"
Cohesion: 0.06
Nodes (17): codes(), m1_raw(), m1_row(), Tests for reference-table schema validation (blocker B2). These test **schema…, The core B2 protection: a cross-check pair must not be all-pipeline., Build `Obot/Ibot/Itop/Otop` readings whose bisected mean is exactly h_mm., M1 = the frozen microscope transition-band bisection (§4.1). These tests check…, The whole point of M1: a symmetric band gives the same height. (+9 more)

### Community 2 - "Glyph Glyph Selection"
Cohesion: 0.07
Nodes (15): check(), codes(), glyph_map(), nominal_runs(), panels(), Tests for the pre-registered panel -> measured-glyph assignment (blocker B5).…, Every claim made in the design write-up, asserted., selection() (+7 more)

### Community 3 - "Physical Analyzer Verification"
Cohesion: 0.06
Nodes (53): mean(), sd(), _esc(), _fmtnum(), histogram(), _nice(), Plot, Minimal dependency-free SVG diagnostic plots. matplotlib is unavailable in this… (+45 more)

### Community 4 - "Setup Gate (B2 Setup Gate)"
Cohesion: 0.06
Nodes (16): failed_codes(), Tests for the B2 pre-capture setup gate. These test the **gate logic only**. No…, The gate must be satisfiable, or it is not a gate., `frame_in_scan` must be explicitly false, not merely absent., An instrument is not acceptable because it sounds high-resolution., A hypothetical fully-verified setup. Not a claim that it exists., satisfied(), TestCli (+8 more)

### Community 5 - "Flatness Acceptance Check"
Cohesion: 0.08
Nodes (20): bound(), codes(), passing_panel(), Tests for the B4 pre-capture flatness acceptance. These test the **acceptance…, The closed form must reproduce what out/synthetic already measured., A gap implying more than the budgeted tilt is a FAIL, not a warning., 0.26 mm over 20 mm is the same tilt as 0.66 mm over 50 mm., Relaxing the mechanical rule would invalidate every emitted interval. (+12 more)

### Community 6 - "Inventory & Fixture Audit"
Cohesion: 0.07
Nodes (17): codes(), complete(), drop(), first(), Tests for the B6 equipment / access inventory gate. These test the **inventory…, §13 files it under PREFERRED; its own MISSING row makes it binding., A guard against the catalogue growing equipment nobody asked for., A hypothetical fully-equipped inventory. Not a claim that it exists. (+9 more)

### Community 7 - "SIH Presentation Deck Builder"
Cohesion: 0.10
Nodes (43): chrome(), fill_ratio(), kv(), main(), mark(), panel(), qa(), Build the Inspectra SIH 2026 idea-submission deck (6 slides, official… (+35 more)

### Community 8 - "Core Math & Primitives"
Cohesion: 0.10
Nodes (35): canonical_json(), _chunk(), cross3(), encode_u8(), fmt(), Core utilities: linear algebra, sRGB linearisation, image buffer, PNG IO,…, Deterministic 64-bit seed from arbitrary strings., Decimal string for persisted numbers (no binary float in results). (+27 more)

### Community 9 - "Physical Analyzer Verification"
Cohesion: 0.08
Nodes (12): manifest_run(), nominal_row(), Tests for the physical (P1-P7) analyser. These test the *plumbing and the…, Editing the criteria document must change the verdict., Missing physical data must never become zero and never become PASS., Abstention is an observed outcome, not an implementation failure., Thresholds must come from the frozen document, not from this codebase., TestCriteriaParsing (+4 more)

### Community 10 - "Web UI & Dependencies"
Cohesion: 0.05
Nodes (37): @cloudflare/vite-plugin, @fontsource/ibm-plex-mono, @fontsource/public-sans, oxlint, react-dom, @types/node, @types/react, @types/react-dom (+29 more)

### Community 11 - "Camera Model & Homography"
Cohesion: 0.12
Nodes (23): homography_for_plane(), jacobian(), matvec3(), plane_pose(), pose_looking_at_origin(), Pinhole camera with Brown-Conrady distortion, poses, and plane homographies.…, Camera orbiting the plane origin at distance `z_mm`, oblique by `tilt_deg`. The…, Pose of a surface plane offset by `d_mm` along +Z and tilted by `alpha_deg`.… (+15 more)

### Community 12 - "Camera Model & Homography"
Cohesion: 0.10
Nodes (26): Angle between the plane normal and the camera optical axis, from H., view_tilt_deg(), mat3_inv(), Gauss-Jordan with partial pivoting. A: list of rows, b: list., solve(), _convex_hull(), _dlt(), fit_homography() (+18 more)

### Community 13 - "Synthetic Rendering & Grid"
Cohesion: 0.12
Nodes (28): plane_to_distorted_px(), apply_h(), marker_bit_grid(), Full CELLS x CELLS grid, True = black., _coverage(), glyph_bbox_mm(), glyph_ink_at(), glyph_sdf() (+20 more)

### Community 14 - "Measure Module"
Cohesion: 0.15
Nodes (25): distorted_px_to_plane(), fit_line_tls(), polyfit(), polyval(), Total-least-squares line. Returns (point_on_line, unit_direction, rms)., _bootstrap_extreme(), _crossings(), estimate_baseline_dir() (+17 more)

### Community 15 - "Web UI & Dependencies"
Cohesion: 0.12
Nodes (17): HeroSection(), WorkspacePreviewPanel(), SiteFooter(), NAV_ITEMS, SiteHeader(), DemoVideoPlaceholder(), ResourceLinkCard(), ResourceLinkCardProps (+9 more)

### Community 16 - "Synthetic Rendering & Grid"
Cohesion: 0.15
Nodes (8): Deterministic description of one synthetic capture configuration., SceneSpec, A wrong ROI must abstain, not return a confident wrong height. This is the…, TestMisplacedRoiAbstains, T-01 style acceptance tests on exactly known geometry., d/Z scale error: measured bias must match theory within 15%., A-08: metric scale comes from the surveyed fiducial, not from fx., TestEndToEndSynthetic

### Community 17 - "Verify B2 Setup Module"
Cohesion: 0.20
Nodes (25): as_number(), _caliper(), _decisions(), get(), is_true(), load_evidence(), main(), _microscope() (+17 more)

### Community 18 - "Camera Model & Homography"
Cohesion: 0.14
Nodes (15): Deterministic PRNG (SplitMix64) -- independent of Python version., read_png_gray(), Rng, reprojection_stats(), TestRng, bootstrap(), collect(), main() (+7 more)

### Community 19 - "Validate Selection Module"
Cohesion: 0.15
Nodes (18): load_json(), The old stub was a valid-looking box at the frame centre., glyph_key(), Same canonical form as the reference table (P0_REFERENCE_PROCEDURE.md §6)., allocate(), balance(), build(), main() (+10 more)

### Community 20 - "Synthetic Rendering & Grid"
Cohesion: 0.13
Nodes (21): compute_roi(), fill(), frame_limits(), index_map(), is_placeholder(), main(), panel_to_fiducial(), Exception (+13 more)

### Community 21 - "Flatness Acceptance Check"
Cohesion: 0.17
Nodes (19): as_number(), evaluate_panel(), FlatnessError, height_error_mm(), main(), max_gap_for(), model_bound_deg(), named() (+11 more)

### Community 22 - "Synthetic Rendering & Grid"
Cohesion: 0.16
Nodes (15): obj_hash(), build_budget(), decide(), default_model(), Uncertainty budget and guard-band decision. Design decisions (PHASE0_REVIEW…, Correct for the fiducial plane sitting `thickness_mm` above the print. The…, Guard-band decision using explicit one-sided bounds., Combine the uncertainty budget for one measurement run. (+7 more)

### Community 23 - "Web UI & Dependencies"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 24 - "Synthetic Rendering & Grid"
Cohesion: 0.14
Nodes (15): percentile(), _components(), ControlPoints, detect_frame(), _hull(), ink_at_marker(), _match_code(), _quad_from_hull() (+7 more)

### Community 25 - "Manifest Module"
Cohesion: 0.11
Nodes (17): algorithm_version, fast_mode, fixtures, frames_per_burst, gate_policy_hash, measurand_policy_hash, runs, uncertainty_model (+9 more)

### Community 26 - "Web UI & Dependencies"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 27 - "Reference Table Validation"
Cohesion: 0.20
Nodes (14): read_csv(), agreement_report(), canonical_glyph_id(), glyph_key(), load_table(), main(), parse_m1_readings(), Exception (+6 more)

### Community 28 - "Web UI & Dependencies"
Cohesion: 0.18
Nodes (10): react, ExternalLinkProps, OFFICER_REVIEW_TEXT, OfficerReviewNotice(), PipelineStageDetail(), PipelineStageDetailProps, PipelineStepper(), PipelineStepperProps (+2 more)

### Community 29 - "Camera Model & Homography"
Cohesion: 0.22
Nodes (3): Camera, Distorted pixel -> ideal pixel (equivalent of cv2.undistortPoints with P=K)., Ideal pixel -> distorted pixel.

### Community 30 - "Web UI & Dependencies"
Cohesion: 0.17
Nodes (12): EvidenceRecordCard(), PREDICATE_TONE, EvidenceTimeline(), AbstentionReason, EvidenceRecord, GateStage, MeasurementDecision, PACKAGE_STATUS_LABEL (+4 more)

### Community 31 - "Glyph Make Glyph Map"
Cohesion: 0.22
Nodes (13): build(), col_pitch_mm(), default_panels_path(), load_panels(), main(), panel_layout(), Derive the pre-registered glyph map for the printed coupons (blocker B3).…, Vertical step after a height row -- `coupon()`: max(h * 1.9, 7.0). (+5 more)

### Community 32 - "Inventory & Fixture Audit"
Cohesion: 0.21
Nodes (11): evidence_fields(), InventoryError, main(), named(), Exception, What must be filled in for this item to count as available., Physical equipment / access inventory gate (blocker B6). `P0_EXECUTION_PLAN.md`…, A blank inventory: every mandatory item present as a record, all fields null. (+3 more)

### Community 33 - "Web UI & Dependencies"
Cohesion: 0.23
Nodes (8): SectionContainer(), SectionContainerProps, BUILT, DESIGNED_ONLY, ProductSection(), Eyebrow(), pipelineStages, sampleEvidenceRecords

### Community 34 - "Web UI & Dependencies"
Cohesion: 0.27
Nodes (9): AbstentionCard(), AbstentionCardProps, ExampleKey, EXAMPLES, sampleAbstention, sampleMeasurementAccepted, sampleMeasurementBorderline, sampleMeasurementUndersize (+1 more)

### Community 35 - "Physical Analyzer Verification"
Cohesion: 0.27
Nodes (9): build(), m1_raw_readings(), main(), Generate the STAND-IN PHYSICAL_PILOT dataset used to test analyser plumbing.…, `Obot/Ibot/Itop/Otop` per re-setting, bottom boundary placed at stage 0., _row(), dump_json(), main() (+1 more)

### Community 36 - "Core Math & Primitives"
Cohesion: 0.24
Nodes (4): Img, Single channel image. `lin` holds linear luminance in [0,1]., Separable Gaussian restricted to a rectangle (outside assumed flat)., TestPng

### Community 37 - "Setup Gate (Gates)"
Cohesion: 0.33
Nodes (6): default_gate_policy(), evaluate(), Monotonic gate evaluation and the MEASURE / ABSTAIN state machine. Every gate…, Evaluate all gates from an aggregated context dictionary., status_from(), TestGates

### Community 38 - "Web UI & Dependencies"
Cohesion: 0.33
Nodes (6): PendingValidationNotice(), STATUS_TONE, SyntheticMetricCard(), undetectableDefectFinding, validationMetrics, ValidationMetric

### Community 39 - "Camera Model & Homography"
Cohesion: 0.22
Nodes (9): lstsq(), mad_sigma(), median(), Least squares via normal equations (rows: m x n, rhs: m)., Robust sigma estimate via median absolute deviation., _homography_from_quad(), Minimal 4-point homography src->dst (unit square style), plain DLT., Sample the 4x4 code grid; returns bits (row major) or None. (+1 more)

### Community 40 - "Web UI & Dependencies"
Cohesion: 0.28
Nodes (7): DECISION_TONE, MeasurementResultCard(), MeasurementResultCardProps, StatusBadge(), StatusBadgeProps, StatusTone, MeasurementResult

### Community 41 - "Web UI & Dependencies"
Cohesion: 0.32
Nodes (5): App(), EvidenceSection(), MeasurementPanelSection(), PrototypeStatusBanner(), ValidationSection()

### Community 42 - "Synthetic Rendering & Grid"
Cohesion: 0.33
Nodes (6): _build_dictionary(), _hamming(), Rotate a 4x4 bit list (row major) by 90 degrees clockwise., Deterministic greedy dictionary with rotation-aware Hamming distance., _rot90(), TestFiducialDictionary

### Community 43 - "Fiducial Module"
Cohesion: 0.33
Nodes (6): _cross_in_profile(), DetectError, Exception, Fit a subpixel line to each quad edge; return the 4 corner intersections. For…, First subpixel crossing of `level` in a sampled (t, value) profile., _refine_edges()

### Community 45 - "Make Coupons Svg Module"
Cohesion: 0.38
Nodes (5): coupon(), glyph_paths(), main(), Emit printable 1:1 coupon sheets for the 20-panel physical pilot. Each coupon…, Draw a glyph of exact ink height `h` mm with its centre at (x, y).

### Community 46 - "Synthetic Rendering & Grid"
Cohesion: 0.40
Nodes (3): build(), main(), Emit a printable 1:1 SVG template of the NDFID-1 fiducial frame. Print at…

### Community 47 - "Web UI & Dependencies"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 48 - "Experiments Module"
Cohesion: 0.60
Nodes (4): _fx(), Deterministic definition of the P0-min synthetic experiment suite.…, suite(), summary()

## Knowledge Gaps
- **113 isolated node(s):** `algorithm_version`, `fast_mode`, `fixtures`, `frames_per_burst`, `gate_policy_hash` (+108 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 426 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_json()` connect `Validate Selection Module` to `Synthetic Rendering & Grid`, `Inventory & Fixture Audit`, `Glyph Glyph Selection`, `Physical Analyzer Verification`, `Setup Gate (B2 Setup Gate)`, `Flatness Acceptance Check`, `Inventory & Fixture Audit`, `Core Math & Primitives`, `Camera Model & Homography`, `Synthetic Rendering & Grid`, `Synthetic Rendering & Grid`, `Verify B2 Setup Module`, `Camera Model & Homography`, `Synthetic Rendering & Grid`, `Flatness Acceptance Check`, `Reference Table Validation`, `Glyph Make Glyph Map`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `dump_json()` connect `Physical Analyzer Verification` to `Synthetic Rendering & Grid`, `Inventory & Fixture Audit`, `Glyph Glyph Selection`, `Physical Analyzer Verification`, `Setup Gate (B2 Setup Gate)`, `Flatness Acceptance Check`, `Inventory & Fixture Audit`, `Core Math & Primitives`, `Physical Analyzer Verification`, `Verify B2 Setup Module`, `Camera Model & Homography`, `Validate Selection Module`, `Synthetic Rendering & Grid`, `Flatness Acceptance Check`, `Synthetic Rendering & Grid`, `Reference Table Validation`, `Glyph Make Glyph Map`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Why does `check()` connect `Synthetic Rendering & Grid` to `Validate Selection Module`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Camera` (e.g. with `measure_run()` and `process_frame()`) actually correct?**
  _`Camera` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `algorithm_version`, `fast_mode`, `fixtures` to the rest of the system?**
  _113 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Synthetic Rendering & Grid` be split into smaller, more focused modules?**
  _Cohesion score 0.08235294117647059 - nodes in this community are weakly interconnected._
- **Should `Reference Table Validation` be split into smaller, more focused modules?**
  _Cohesion score 0.06376726417866588 - nodes in this community are weakly interconnected._