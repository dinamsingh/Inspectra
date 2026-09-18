# P0-min physical experiment protocol (20 panels)

> **Do not start capturing from this document alone.**  The execution-readiness audit
> in [`P0_EXECUTION_PLAN.md`](P0_EXECUTION_PLAN.md) freezes the operational details this
> protocol leaves open (vocabulary, run/observation counts, ordering, naming, failure
> handling, P1–P7 mapping) and currently reports
> `PHYSICAL_EXPERIMENT_READY = NO` with six open blockers.  Close those first.

Purpose: answer, with physical evidence, whether a normal Android smartphone can
estimate printed glyph ink extent in millimetres with useful repeatability and
error, and abstain when conditions are unsafe.  Success criteria are in
`docs/P0_CRITERIA.md` (P1-P7).  Nothing in this protocol requires an app: the
phone is used only as a camera.

## 0. Bill of materials

| Item | Spec | Note |
|---|---|---|
| Fiducial frame | `tools/make_frame_svg.py`, printed 1:1 on polyester film or laser-engraved acrylic; outer 100 x 60 mm, 10 mm markers, 50 x 20 mm window | dimensional stability matters more than print quality |
| Rigid backing | float glass or ground aluminium plate, >= 150 x 100 mm | defines the flat print plane |
| Coupons | `tools/make_coupons_svg.py`, 20 panels, heights 1.2/2.0/3.0/4.0/6.0 mm, 4 shapes, 4 fonts | mount flat on the backing |
| Digital caliper | resolution 0.01 mm, with a calibration record | frame survey + frame thickness |
| Reference instrument | flatbed scanner at 2400 dpi **and** a measuring microscope or toolmaker's microscope for a cross-check subset | see section 3 |
| Calibrated scale / graticule | steel rule or glass graticule with a certificate | calibrates the scanner |
| Phones | 2 devices, manual/pro camera app | must allow AF lock and HDR off |
| Copy stand or tripod | with a sliding head | repeat captures must not move the panel |
| Lighting | two diffuse sources at ~45 degrees, no direct specular path | cross-polarisers optional for glossy stock |

## 1. Frame preparation and survey

1. Print the frame at exactly 100 percent.  Verify the 100.000 mm check bar with
   the caliper; if it is off by more than 1 percent, the printer is scaling --
   fix it before continuing.
2. Cut out the window.  Laminate or mount on rigid board so it cannot bow.
3. Measure the **frame thickness** at four places; record mean and spread.
4. Survey, 10 repeats each:
   * centre-to-centre span of the left and right marker columns;
   * centre-to-centre span of the top and bottom marker rows;
   * marker side length (mean of the four markers).
5. Write the certificate:
   ```
   python3 tools/survey_frame.py --serial FRAME-0001 \
     --cx-span <mm> --cy-span <mm> --side <mm> --thickness <mm> \
     --u-span <sd> --u-side <sd> --u-thickness <sd> \
     --instrument "<make, model, cal date>" \
     --out config/frames/FRAME-0001.json
   ```
6. Record the flatness you can actually verify over the window (feeler / straight
   edge).  A caliper survey does **not** characterise out-of-plane form; see
   `docs/P0_ASSUMPTIONS.md` A-06.

**Why a caliper is enough:** a 0.02 mm survey uncertainty over a ~100 mm baseline
is a 0.02 percent scale error, i.e. 0.0006 mm on a 3 mm glyph -- about 250 times
smaller than the accuracy target.  A CMM is a nice-to-have, not a blocker.

## 2. Camera profiles

For each phone, each rear camera, each resolution and each focus/zoom mode:

1. Lock the **physical camera id** (many phones silently switch to a macro or
   ultra-wide module at close focus -- that is a different lens).
2. Disable HDR, night mode, beauty, and OIS/EIS if the app allows it.  Record
   whether OIS could actually be disabled.
3. Lock AF at the working distance, lock AE and AWB.
4. Capture >= 12 views of the frame at varied tilt, roll, azimuth and lateral
   position, keeping the whole frame inside the image.
5. Convert to PNG and run:
   ```
   python3 tools/calibrate_camera.py --images caps/calib/PHONE-A \
     --frame config/frames/FRAME-0001.json --width 4000 --height 3000 \
     --profile-id PHONE-A_main_4000x3000 --device-model "<model>" \
     --z-calib-mm 200 --out config/cameras/PHONE-A.json
   ```
6. Record the achieved residual.  Note that the estimated focal length is **not**
   metrologically meaningful (A-08); only the distortion removal matters.

## 3. Reference (ground truth) measurement

Ground truth must implement the *same* measurand as the pipeline: the 50 percent
linearised-luminance ink boundary, measured perpendicular to the baseline.

**Primary: flatbed scanner at 2400 dpi (94.5 px/mm).**
1. Calibrate the scanner scale in both axes against the certified scale/graticule;
   record the scale factors and any non-uniformity across the platen.
2. Scan each coupon flat, 8-bit greyscale, all enhancement off, 2400 dpi.
3. Measure each glyph with the same estimator (the scan is just a very high-rho
   capture; record the procedure and the software version used).
   **Count:** the generated coupons carry 4 shapes x 5 heights per panel, so 20 panels
   contain **400 glyph instances**.  Measuring all 400 is the reference target; if that
   is not achievable, the reduced set must be *pre-declared* (for example one shape per
   height per panel = 100 glyphs) and the reduction recorded with the results.  Do not
   decide the subset after seeing camera data.
4. Reference uncertainty target: <= 0.01 mm, i.e. about one third of the intended
   system uncertainty or better.

**Cross-check: measuring microscope on >= 15 glyphs spanning heights and fonts.**
Compute the mean absolute scanner-vs-microscope difference -- this is criterion
P1.  If it exceeds 0.06 mm, stop: there is no usable ground truth and no accuracy
claim can be made.

**Never** use the nominal height from the SVG as ground truth; printer scaling and
ink spread change the real ink extent.

## 4. Capture matrix

* 20 panels x 2 devices x 2 operators x 3 repeats = **240 nominal runs**.
* Each run is a **burst of 7 frames** (the burst is what produces the live
  repeatability term; do not substitute a single frame).
* Angles are assigned across repeats: repeat 1 = 0 deg, repeat 2 = 12 deg,
  repeat 3 = 25 deg.  Do **not** plan a 35 deg accuracy block: the synthetic sweep
  already abstained at 30 deg and lost detection at 40 deg, and depth of field at
  close range makes large tilts optically infeasible.
* Working distance: keep sampling density at **>= 16 px/mm** at the glyph.  The
  synthetic sweep showed the pre-registered blur gate (sigma <= 0.06 mm) is
  unreachable below roughly 15-16 px/mm with a realistic PSF, so the review's
  earlier "rho >= 12 px/mm" figure is too low.
* Operators must not adjust the frame between the 7 frames of a burst.
* Record for every run: panel id, device, operator, repeat, angle, working
  distance, whether OIS was disabled, lighting, conversion command, and which
  glyph (shape + index) was measured.

### Stress block (about 60 runs, separate)
Minimum 8 runs each of: defocus, motion blur, specular glare on the glyph,
partially occluded marker, wrong frame serial, low-contrast print, bowed panel
(deliberately unclamped), frame not flush (a shim under one edge).

These runs have **no accuracy expectation**; they test criterion P6 (unsafe
acceptance) and the abstention reasons.

## 5. Directory layout and execution

```
caps/
  calib/PHONE-A/*.png
  <panel>/<device>/<operator>/<repeat>/f0.png ... f6.png
```
```
python3 tools/run_real_batch.py --scaffold caps --out manifests/pilot.json
#   fill in roi_mm, shape_class, glyph_label, reference_h_mm, reference_method, angle_deg
python3 tools/run_real_batch.py --manifest manifests/pilot.json --out out/pilot
python3 tools/analyse_results.py --in out/pilot
```

## 6. Analysis (pre-registered)

1. Signed error vs reference, by device, font, stock, height and angle.
2. Repeatability SD within (panel, device, operator); between operators; between
   devices.
3. Residual SD after a **single global** bias correction, then after a per-device
   correction.  The difference is the device-effect evidence (criterion P4).
4. Gate acceptance rate per condition and the abstention-reason histogram.
5. Does the live burst spread predict the actual error?  (Correlation of
   `burst_sd_mm` with `abs_error_mm`.)
6. Empirical interval coverage; fit `k` on the development split only and report
   coverage on the held-back split.

## 7. Reporting rule

Report accuracy and abstention **together**, always.  An accuracy figure computed
only over non-abstained runs, without the abstention rate, is not a result.

## 8. What this protocol cannot establish

* Out-of-plane print error (A-06) -- controlled by the fixture, not measured.
* Any statutory character-height conclusion (A-09).
* Performance on curved, moulded, embossed or creased surfaces -- out of scope.
* Generalisation beyond the two tested devices, four fonts and two stocks.
