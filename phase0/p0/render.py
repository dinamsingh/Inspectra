"""Synthetic scene renderer with exactly known ground-truth glyph geometry.

The renderer is the scientific backbone of P0-min: because the ink region is
defined analytically as {signed_distance < ink_spread}, the true ink extent of
every glyph is known in closed form, so pipeline error can be separated from
physical measurement uncertainty.

Rendering model (in this order):
  1. ink coverage by supersampling an analytic signed-distance field, evaluated
     through the *exact* inverse plane homography (no intermediate bitmap);
  2. reflectance  = paper*(1-coverage) + ink*coverage   [linear light];
  3. illumination field (gradient / vignette);
  4. additive specular glare blob;
  5. point spread function (Gaussian, optionally anisotropic = motion);
  6. optional unsharp mask, modelling phone ISP sharpening overshoot;
  7. sensor noise, clipping, then sRGB encoding to 8-bit.

Only the marker patches and the glyph patch are rendered at full supersampling;
the rest of the canvas is uniform paper.  This is an exact optimisation for the
measured quantities (A-04).
"""
from __future__ import annotations

import math

from .camera import (Camera, homography_for_plane, plane_to_distorted_px,
                     pose_looking_at_origin)
from .core import Img, Rng, apply_h, mat3_inv
from .fiducial import CELLS, marker_bit_grid

# --------------------------------------------------------------------------
# glyph signed distance fields (plane mm, centred on the origin)
# --------------------------------------------------------------------------


def _sdf_box(x, y, hx, hy):
    dx = abs(x) - hx
    dy = abs(y) - hy
    ox = dx if dx > 0.0 else 0.0
    oy = dy if dy > 0.0 else 0.0
    outside = math.sqrt(ox * ox + oy * oy)
    inside = min(max(dx, dy), 0.0)
    return outside + inside


def _sdf_ellipse(x, y, a, b):
    """First-order distance to an ellipse; exact on the principal axes."""
    if a <= 0.0 or b <= 0.0:
        return 1e9
    f = math.sqrt((x / a) ** 2 + (y / b) ** 2) - 1.0
    gx = x / (a * a)
    gy = y / (b * b)
    g = math.sqrt(gx * gx + gy * gy)
    if g < 1e-12:
        return -min(a, b)
    return f / g


GLYPH_SHAPES = ("BAR_I", "H", "T", "RING_O")


def glyph_sdf(shape, x, y, h):
    """Signed distance to the nominal glyph outline of design height `h` mm."""
    if shape == "BAR_I":
        return _sdf_box(x, y, 0.09 * h, 0.5 * h)
    if shape == "H":
        stem = 0.08 * h
        d = min(_sdf_box(x - 0.32 * h, y, stem, 0.5 * h),
                _sdf_box(x + 0.32 * h, y, stem, 0.5 * h))
        return min(d, _sdf_box(x, y, 0.32 * h, 0.075 * h))
    if shape == "T":
        return min(_sdf_box(x, y - 0.425 * h, 0.40 * h, 0.075 * h),
                   _sdf_box(x, y, 0.08 * h, 0.5 * h))
    if shape == "RING_O":
        a, b = 0.35 * h, 0.5 * h
        t = 0.13 * h
        outer = _sdf_ellipse(x, y, a, b)
        inner = _sdf_ellipse(x, y, max(a - t, 1e-3), max(b - t, 1e-3))
        return max(outer, -inner)
    raise ValueError("unknown glyph shape %r" % shape)


def glyph_ink_at(shape, x, y, h, spread):
    """Exact ink membership test for the rendered glyph.

    Ink spread is modelled as a real geometric growth of the outline, not as an
    offset of an approximate signed-distance field: for the ellipse ring the
    semi-axes are grown/shrunk directly, because the first-order ellipse distance
    is only exact on the principal axes and its level sets bulge off-axis.  The
    test `test_true_height_is_exact_for_every_shape` falsified the earlier
    SDF-offset version, so the ground truth stays closed form.
    """
    if shape == "RING_O":
        a, b = 0.35 * h, 0.5 * h
        t = 0.13 * h
        ao, bo = a + spread, b + spread
        ai = max(a - t - spread, 1e-9)
        bi = max(b - t - spread, 1e-9)
        if (x / ao) ** 2 + (y / bo) ** 2 > 1.0:
            return False
        return (x / ai) ** 2 + (y / bi) ** 2 >= 1.0
    return glyph_sdf(shape, x, y, h) < spread


def glyph_shape_class(shape):
    return "FLAT_TOP" if shape in ("BAR_I", "H", "T") else "ROUND"


def true_ink_height_mm(shape, design_h, ink_spread_mm):
    """Exact height of {sdf < ink_spread}; verified by test_render_groundtruth."""
    return design_h + 2.0 * ink_spread_mm


def glyph_bbox_mm(shape, design_h, ink_spread_mm):
    h = true_ink_height_mm(shape, design_h, ink_spread_mm)
    if shape == "H":
        w = 2 * (0.40 * design_h) + 2 * ink_spread_mm
    elif shape == "T":
        w = 2 * (0.40 * design_h) + 2 * ink_spread_mm
    elif shape == "RING_O":
        w = 2 * (0.35 * design_h) + 2 * ink_spread_mm
    else:
        w = 2 * (0.09 * design_h) + 2 * ink_spread_mm
    return w, h


# --------------------------------------------------------------------------
# scene specification
# --------------------------------------------------------------------------


class SceneSpec:
    """Deterministic description of one synthetic capture configuration."""

    def __init__(self, **kw):
        self.z_mm = kw.get("z_mm", 200.0)
        self.tilt_deg = kw.get("tilt_deg", 0.0)
        self.azimuth_deg = kw.get("azimuth_deg", 0.0)
        self.roll_deg = kw.get("roll_deg", 0.0)
        self.shift_mm = kw.get("shift_mm", (0.0, 0.0))
        # glyph
        self.glyph_shape = kw.get("glyph_shape", "BAR_I")
        self.design_h_mm = kw.get("design_h_mm", 3.0)
        self.ink_spread_mm = kw.get("ink_spread_mm", 0.0)
        self.glyph_center_mm = kw.get("glyph_center_mm", (0.0, 0.0))
        self.halftone_pitch_mm = kw.get("halftone_pitch_mm", 0.0)
        # surface of the glyph relative to the fiducial plane
        self.glyph_plane_offset_mm = kw.get("glyph_plane_offset_mm", 0.0)
        self.glyph_plane_tilt_deg = kw.get("glyph_plane_tilt_deg", 0.0)
        # photometry
        self.paper_reflect = kw.get("paper_reflect", 0.82)
        self.ink_reflect = kw.get("ink_reflect", 0.04)
        self.illum_gain = kw.get("illum_gain", 1.0)
        self.illum_gradient = kw.get("illum_gradient", 0.0)
        self.glare = kw.get("glare", None)     # dict(x_mm,y_mm,sigma_mm,amp)
        # optics / sensor
        self.blur_sigma_px = kw.get("blur_sigma_px", 0.8)
        self.blur_sigma_px_y = kw.get("blur_sigma_px_y", None)
        self.unsharp_amount = kw.get("unsharp_amount", 0.0)
        self.unsharp_radius_px = kw.get("unsharp_radius_px", 1.5)
        self.noise_sigma = kw.get("noise_sigma", 0.002)
        # frame content overrides (negative fixtures)
        self.marker_ids = kw.get("marker_ids", None)     # None = cert ids
        self.drop_markers = kw.get("drop_markers", ())
        # sampling
        self.ss_marker = kw.get("ss_marker", 3)
        self.ss_glyph = kw.get("ss_glyph", 4)
        # per frame jitter (applied by render_burst)
        self.jitter_pos_mm = kw.get("jitter_pos_mm", 0.35)
        self.jitter_ang_deg = kw.get("jitter_ang_deg", 0.20)
        self.jitter_z_mm = kw.get("jitter_z_mm", 0.8)

    def to_dict(self):
        d = dict(self.__dict__)
        d["shift_mm"] = list(self.shift_mm)
        d["glyph_center_mm"] = list(self.glyph_center_mm)
        d["drop_markers"] = list(self.drop_markers)
        if self.marker_ids is not None:
            d["marker_ids"] = list(self.marker_ids)
        return d


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------


def _coverage(px, py, ink_fn, ss, force_full=False):
    """Adaptive analytic-ish ink coverage of pixel (px, py).

    A pixel spans [px-0.5, px+0.5) x [py-0.5, py+0.5).  Interior pixels are
    decided from five probes; only pixels that straddle an ink boundary are
    supersampled `ss x ss`.  This keeps the rendered edge position accurate to
    roughly 1/(2*ss) of a pixel, which matters because a coarse coverage
    quantisation would otherwise masquerade as measurement error.
    """
    if not force_full:
        e = 0.499
        c = ink_fn(px, py)
        if (ink_fn(px - e, py - e) == c and ink_fn(px + e, py - e) == c
                and ink_fn(px - e, py + e) == c and ink_fn(px + e, py + e) == c):
            return 1.0 if c else 0.0
    inv = 1.0 / ss
    hit = 0
    for sy in range(ss):
        vv = py - 0.5 + (sy + 0.5) * inv
        for sx in range(ss):
            if ink_fn(px - 0.5 + (sx + 0.5) * inv, vv):
                hit += 1
    return hit / float(ss * ss)


def _region_for_plane_rect(cam, H, x0, y0, x1, y1, margin_px, w, h):
    us, vs = [], []
    n = 5
    for i in range(n + 1):
        for j in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            y = y0 + (y1 - y0) * j / n
            u, v = plane_to_distorted_px(cam, H, x, y)
            us.append(u)
            vs.append(v)
    return (max(int(math.floor(min(us))) - margin_px, 0),
            max(int(math.floor(min(vs))) - margin_px, 0),
            min(int(math.ceil(max(us))) + margin_px, w),
            min(int(math.ceil(max(vs))) + margin_px, h))


def render_frame(cam: Camera, frame_cert, spec: SceneSpec, rng: Rng,
                 pose=None):
    """Render one image.  Returns (Img, ground_truth_dict)."""
    if pose is None:
        pose = pose_looking_at_origin(spec.z_mm, spec.tilt_deg, spec.azimuth_deg,
                                      spec.roll_deg, spec.shift_mm)
    R, t = pose
    H_frame = homography_for_plane(cam, R, t, 0.0, 0.0)
    H_glyph = homography_for_plane(cam, R, t, spec.glyph_plane_offset_mm,
                                   spec.glyph_plane_tilt_deg)
    Hi_frame = mat3_inv(H_frame)
    Hi_glyph = mat3_inv(H_glyph)

    img = Img(cam.width, cam.height, spec.paper_reflect)
    blur_margin = int(math.ceil(4.0 * max(spec.blur_sigma_px,
                                          spec.blur_sigma_px_y or 0.0,
                                          spec.unsharp_radius_px))) + 3

    ids = list(spec.marker_ids if spec.marker_ids is not None
               else frame_cert["expected_marker_ids"])
    regions = []
    gt_corners = {}

    # ---- markers --------------------------------------------------------
    for slot, mid in enumerate(ids):
        cert_id = frame_cert["expected_marker_ids"][slot]
        if cert_id in spec.drop_markers or slot in spec.drop_markers:
            continue
        corners = frame_cert["markers"][str(cert_id)]["corners_mm"]
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        side = x1 - x0
        grid = marker_bit_grid(mid)
        reg = _region_for_plane_rect(cam, H_frame, x0, y0, x1, y1,
                                     blur_margin, cam.width, cam.height)
        regions.append(reg)
        gt_corners[cert_id] = [plane_to_distorted_px(cam, H_frame, cx, cy)
                               for cx, cy in corners]
        rx0, ry0, rx1, ry1 = reg
        paper = spec.paper_reflect
        ink = spec.ink_reflect
        und = cam.undistort_px if cam.has_distortion else None

        def marker_ink(uu, vv, _x0=x0, _y1=y1, _side=side, _grid=grid):
            if und is not None:
                uu, vv = und(uu, vv)
            X, Y = apply_h(Hi_frame, uu, vv)
            fx = (X - _x0) / _side
            fy = (_y1 - Y) / _side
            if 0.0 <= fx < 1.0 and 0.0 <= fy < 1.0:
                return _grid[int(fy * CELLS)][int(fx * CELLS)]
            return False

        for py in range(ry0, ry1):
            row = py * img.w
            for px in range(rx0, rx1):
                c = _coverage(px, py, marker_ink, spec.ss_marker)
                if c > 0.0:
                    img.lin[row + px] = paper * (1.0 - c) + ink * c

    # ---- glyph ----------------------------------------------------------
    gw, gh = glyph_bbox_mm(spec.glyph_shape, spec.design_h_mm, spec.ink_spread_mm)
    gcx, gcy = spec.glyph_center_mm
    pad = max(0.35 * gh, 1.2)
    greg = _region_for_plane_rect(cam, H_glyph, gcx - gw / 2 - pad, gcy - gh / 2 - pad,
                                  gcx + gw / 2 + pad, gcy + gh / 2 + pad,
                                  blur_margin, cam.width, cam.height)
    regions.append(greg)
    rx0, ry0, rx1, ry1 = greg
    shape = spec.glyph_shape
    dh = spec.design_h_mm
    spread = spec.ink_spread_mm
    pitch = spec.halftone_pitch_mm
    paper = spec.paper_reflect
    ink = spec.ink_reflect
    und = cam.undistort_px if cam.has_distortion else None

    def glyph_ink(uu, vv):
        if und is not None:
            uu, vv = und(uu, vv)
        X, Y = apply_h(Hi_glyph, uu, vv)
        if not glyph_ink_at(shape, X - gcx, Y - gcy, dh, spread):
            return False
        if pitch > 0.0:
            kx = int(math.floor((X - gcx) / pitch))
            ky = int(math.floor((Y - gcy) / pitch))
            if (kx + ky) % 2:
                return False
        return True

    force = pitch > 0.0          # sub-pixel dither must not be adaptively skipped
    for py in range(ry0, ry1):
        row = py * img.w
        for px in range(rx0, rx1):
            c = _coverage(px, py, glyph_ink, spec.ss_glyph, force_full=force)
            if c > 0.0:
                img.lin[row + px] = paper * (1.0 - c) + ink * c

    # ---- photometric degradations --------------------------------------
    for (rx0, ry0, rx1, ry1) in regions:
        if spec.illum_gain != 1.0 or spec.illum_gradient != 0.0:
            for py in range(ry0, ry1):
                row = py * img.w
                for px in range(rx0, rx1):
                    g = spec.illum_gain * (1.0 + spec.illum_gradient *
                                           (px - cam.cx) / max(cam.width, 1))
                    img.lin[row + px] *= g
        if spec.glare:
            gx, gy = plane_to_distorted_px(cam, H_frame, spec.glare["x_mm"],
                                           spec.glare["y_mm"])
            rho = cam.f_px / max(spec.z_mm, 1e-6)
            sig = max(spec.glare["sigma_mm"] * rho, 1.0)
            amp = spec.glare["amp"]
            for py in range(ry0, ry1):
                row = py * img.w
                dy = py - gy
                for px in range(rx0, rx1):
                    dx = px - gx
                    e = (dx * dx + dy * dy) / (2.0 * sig * sig)
                    if e < 12.0:
                        img.lin[row + px] += amp * math.exp(-e)

    for (rx0, ry0, rx1, ry1) in regions:
        img.blur_rect(rx0, ry0, rx1, ry1, spec.blur_sigma_px, spec.blur_sigma_px_y)

    if spec.unsharp_amount > 0.0:
        for (rx0, ry0, rx1, ry1) in regions:
            base = [img.lin[py * img.w + px]
                    for py in range(ry0, ry1) for px in range(rx0, rx1)]
            img.blur_rect(rx0, ry0, rx1, ry1, spec.unsharp_radius_px)
            i = 0
            a = spec.unsharp_amount
            for py in range(ry0, ry1):
                row = py * img.w
                for px in range(rx0, rx1):
                    lo = img.lin[row + px]
                    v = base[i] + a * (base[i] - lo)
                    img.lin[row + px] = 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)
                    i += 1

    for (rx0, ry0, rx1, ry1) in regions:
        img.add_noise_rect(rx0, ry0, rx1, ry1, spec.noise_sigma, rng)

    for i in range(len(img.lin)):
        v = img.lin[i]
        if v < 0.0:
            img.lin[i] = 0.0
        elif v > 1.0:
            img.lin[i] = 1.0

    gt = {
        "true_ink_height_mm": true_ink_height_mm(shape, dh, spread),
        "design_h_mm": dh,
        "ink_spread_mm": spread,
        "glyph_shape": shape,
        "shape_class": glyph_shape_class(shape),
        "glyph_center_mm": [gcx, gcy],
        "glyph_bbox_mm": [gw, gh],
        "marker_corner_px": {str(k): [[u, v] for (u, v) in val]
                             for k, val in gt_corners.items()},
        "pose_z_mm": spec.z_mm,
        "pose_tilt_deg": spec.tilt_deg,
        "glyph_plane_offset_mm": spec.glyph_plane_offset_mm,
        "glyph_plane_tilt_deg": spec.glyph_plane_tilt_deg,
        "rho_nominal_px_per_mm": cam.f_px / max(spec.z_mm, 1e-9),
    }
    return img, gt


def render_burst(cam: Camera, frame_cert, spec: SceneSpec, fixture_id: str, n=7):
    """Render `n` frames with realistic pose jitter and independent noise."""
    from .core import seed_from
    frames = []
    gts = []
    for k in range(n):
        rng = Rng(seed_from(fixture_id, "frame", k))
        z = spec.z_mm + rng.normal(0.0, spec.jitter_z_mm)
        tilt = spec.tilt_deg + rng.normal(0.0, spec.jitter_ang_deg)
        azim = spec.azimuth_deg + rng.normal(0.0, spec.jitter_ang_deg)
        roll = spec.roll_deg + rng.normal(0.0, spec.jitter_ang_deg)
        shift = (spec.shift_mm[0] + rng.normal(0.0, spec.jitter_pos_mm),
                 spec.shift_mm[1] + rng.normal(0.0, spec.jitter_pos_mm))
        pose = pose_looking_at_origin(z, tilt, azim, roll, shift)
        img, gt = render_frame(cam, frame_cert, spec, rng, pose=pose)
        gt["frame_index"] = k
        gt["frame_pose"] = {"z_mm": z, "tilt_deg": tilt, "azimuth_deg": azim,
                            "roll_deg": roll, "shift_mm": list(shift)}
        frames.append(img)
        gts.append(gt)
    return frames, gts
