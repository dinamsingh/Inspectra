# P0-min unresolved assumptions and limitations

Each item states what is assumed, why it is unresolved, and what would resolve it.
Nothing here may be presented as settled.

## A-01 No third-party numerical stack
**Assumption:** a pure standard-library implementation is an acceptable reference
for Phase 0.
**Why:** the build environment has no network access, so numpy / OpenCV /
matplotlib cannot be installed.  Every numerical routine (least squares, 3x3
inverse, TLS line fit, homography DLT + Gauss-Newton, distortion inverse, PNG
codec, SVG plots) is therefore implemented and unit tested here.
**Consequence:** speed, not correctness.  A production port should swap in
OpenCV for `detect_frame`, `undistortPoints`, `findHomography` and compare
against the golden fixtures in `fixtures/golden/`.
**Resolves when:** the OpenCV-backed backend reproduces the golden outputs within
the documented replay tolerance.

## A-02 Image input format
**Assumption:** captures are supplied as 8-bit greyscale PNG.
**Why:** a pure-Python JPEG/DNG decoder is out of scope.
**Consequence:** real captures must be converted, e.g.
`magick in.jpg -colorspace Gray -depth 8 out.png`, and any conversion that
applies sharpening or tone mapping will change the measurement.  The conversion
command must be recorded per run.
**Resolves when:** the production client reads sensor data directly.

## A-03 Custom fiducial (NDFID-1) rather than ArUco / ChArUco
**Assumption:** a coded square marker whose control points come from intersecting
subpixel edge-line fits is representative of the production fiducial.
**Why:** cv2.aruco is unavailable (A-01).  The metrological design -- four markers
enclosing the region of interest, edge-line corners, coded identity -- is the part
that matters and is preserved.
**Consequence:** absolute corner-localisation performance may differ from
cv2.aruco / ChArUco.  `ControlPoints` is detector agnostic so only `p0/fiducial.py`
changes.
**Resolves when:** a ChArUco border is implemented and the corner residuals are
compared on the same fixtures.

## A-04 Region-limited rendering
**Assumption:** rendering only the marker patches and the glyph patch (the rest
being uniform paper) does not change the measured quantities.
**Why:** full-canvas supersampling in pure Python is prohibitively slow.
**Consequence:** the synthetic images are not photorealistic scenes; they contain
no other print, no texture and no background clutter, so detector robustness
against clutter is untested.
**Resolves when:** physical captures are processed.

## A-05 Non-planarity is modelled as a tilted / offset plane
**Assumption:** for a glyph a few millimetres across, a bowed carton panel is to
first order a plane that is offset and tilted with respect to the fiducial plane.
**Why:** it keeps every mapping an exact homography and makes the ground truth
closed form.
**Consequence:** true continuous curvature, creases and local dents are untested.
**Resolves when:** physical bowed and creased panels are measured.

## A-06 Out-of-plane print is *not detectable* from a single view
**Status: measured, not assumed.**  In `out/synthetic`, an undeclared 5 mm plane
offset and a 20 degree local print tilt were both MEASURED with reprojection RMS
~0.09-0.12 px and LOMO scale spread ~0.0002 -- i.e. every geometric gate was
comfortably satisfied while the height error reached 0.08 mm and 0.18 mm.
**Consequence:** the review's proposal to replace the impossible absolute
flatness gate with a *local tilt* gate is only partly implementable: view
obliqueness is observable from the homography, but the print plane's tilt
relative to the fiducial plane is not.  It must be guaranteed by the fixture
(flat backing, frame flush, visual rock/gap check) and carried as a bounded
systematic term in the budget.
**Resolves when:** either a second view / stereo cue is added, or the fixture
tolerance is verified mechanically.

## A-07 Coverage factor k is nominal
**Assumption:** `k_lower = k_upper = 1.645` gives ~95 percent one sided coverage.
**Why:** no physical validation data exists yet; the uncertainty model ships
explicitly uncalibrated (`UM-v1-uncalibrated`, bias 0, u_extra 0).
**Consequence:** observed synthetic coverage of 1.00 on n=17 proves only that the
budget is not *optimistic on synthetic data*, where the dominant physical terms
(ink spread, print gain, ISP sharpening, device-to-device bias) are absent.
**Resolves when:** the sealed physical set gives an empirical coverage estimate
and `k` is fitted on the development split only.

## A-08 Focal length is not the scale reference
**Status: measured.**  The calibration self-test recovered `fx` 8.7 percent low
(the classic fx/k1 valley on a coplanar target) yet the resulting height error
changed by 0.0001 mm, because metric scale comes from the surveyed fiducial, not
from the intrinsics.
**Consequence:** intrinsic calibration needs to be good enough to *remove
distortion*, not to be metrologically accurate.  Do not claim a calibrated focal
length.

## A-09 The measurand is not the legal measurand
**Assumption:** "visible printed-ink extent perpendicular to the baseline at the
50 percent linearised luminance boundary" is a useful proxy.
**Why:** the controlling rule's definition of character height (ink extent vs
nominal cap height, which glyphs, which faces) is unverified -- SOLUTION_LOCK_V2
gate G0.
**Consequence:** every output must be labelled as an ink-extent estimate against a
*configured engineering threshold*, never as statutory compliance.

## A-10 Ink spread is geometric growth
**Assumption:** print gain can be modelled as growing the outline by a constant
offset.
**Why:** it makes ground truth exact.  Note that an earlier version offset an
*approximate* ellipse distance field and the ground truth was wrong by 0.005 mm;
`test_true_height_is_exact_for_every_shape` caught it and the model was changed to
grow the semi-axes directly.
**Consequence:** real dot gain is anisotropic, substrate dependent and not a
constant offset.

## A-11 Blur is symmetric
**Assumption:** the PSF is a symmetric Gaussian (or an anisotropic Gaussian for
motion), so the 50 percent crossing is preserved.
**Consequence:** real asymmetric effects -- coma, ISP sharpening overshoot, dot
gain asymmetry -- shift the boundary.  The suite models sharpening explicitly
(`N_SHARPENING`) but not coma.

## A-12 No physical data yet
No coupon has been printed, surveyed or photographed.  Everything reported today
is synthetic.  The 20-panel protocol in `docs/P0_PROTOCOL.md` is the next step and
is the only thing that can support a millimetre accuracy claim.

## A-13 Operator and device variability untested
Two operators, two phones, burst jitter and angle blocks are specified in the
protocol but only *simulated* pose jitter has been exercised.

## A-14 Single glyph per run
The pipeline measures one operator-selected glyph.  The `MIN_ELIGIBLE_GLYPH`
aggregation rule and its selection-bias handling are defined in the policy but not
yet implemented or tested.

## A-15 Determinism scope
Results are bit-identical for the same interpreter, platform and pinned code.
Cross-platform float differences are not eliminated; replay should be compared
with a tolerance (proposed 0.005 mm), not by byte equality.


## A-16 Synthetic runs bypass 8-bit quantisation
**Status: found by the consistency audit.**  `tools/run_experiment.py` passes the
renderer's **in-memory linear float** buffer straight into the pipeline
(`imgs = frames`).  The `frameN.png` written next to each result is 8-bit
sRGB-encoded **evidence only** -- it is not what was measured.
**Consequence:** every synthetic number reported in `out/synthetic` is free of 8-bit
quantisation noise, while physical runs go through `read_png_gray` and therefore
carry it.  The synthetic accuracy figures are correspondingly optimistic, and the
gap is one more reason they cannot be quoted as camera performance.
**Resolves when:** the physical pilot runs, or a synthetic variant is added that
re-reads the quantised PNG.  Not changed now because it would alter the committed,
pre-registered result set.

## A-17 The sampling-density gate floor is not the capture target
`min_rho_px_per_mm = 10.0` in `gate_policy_v1.json` is a pre-registered **hard
floor** and was deliberately not moved after the experiment.  The *operating target*
in `P0_PROTOCOL.md` §4 is **>= 16 px/mm**, because the blur gate
(`max_blur_sigma_mm = 0.06`) binds before the rho gate does with a realistic PSF:
in the rho sweep every working distance beyond 200 mm abstained on blur, not on rho.
Both numbers are correct; they answer different questions.  Do not "reconcile" them
by editing either value.

## A-18 Gate-policy file name versus policy id
`phase0/config/gate_policy_v1.json` carries `policy_id: "GP-v2"`.  This is
intentional: the **file path is a stable slot** that tools load, while the
**`policy_id` tracks the gate-set revision**.  GP-v2 differs from GP-v1 by one
*added* gate (`max_edge_fit_rms_mm`), introduced after run v1 measured a ragged
dithered boundary without abstaining; no existing limit was loosened.  Both runs are
kept (`out/synthetic_v1` = GP-v1, `out/synthetic` = GP-v2).  The file was not renamed
because `policy_hash` is recorded inside every result and renaming would break the
reproducibility of the committed set.
