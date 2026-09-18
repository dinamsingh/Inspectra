"""Scanline boundary estimator and image-quality metrics.

Estimator (the primary one; `max - min` is computed only as a diagnostic):

1. Sample the linear-luminance profile along N scanlines that run parallel to
   the plane-space baseline normal.
2. On each scanline locate the first and last crossing of the boundary level
   `L_ink + f*(L_paper - L_ink)` with subpixel linear interpolation.
3. Map every crossing back through the inverse homography into plane
   millimetres and project it onto the baseline normal.
4. Fit a model to the resulting top / bottom edge point sets -- a robust line
   for FLAT_TOP glyphs, a parabola vertex for ROUND glyphs -- and take the
   distance between the fitted extremes.
5. Bootstrap the scanline points to obtain the standard error of each fitted
   extreme.

Why not `max - min`: extreme order statistics inflate the height as noise grows,
which makes the estimate device and blur dependent (PHASE0_REVIEW F1.1).
"""
from __future__ import annotations

import math

from .camera import distorted_px_to_plane, plane_to_distorted_px
from .core import (Rng, fit_line_tls, mad_sigma, mean, median, percentile,
                   polyfit, polyval, sd, seed_from)


class MeasureError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code + (": " + detail if detail else ""))
        self.code = code
        self.detail = detail


def _sample_profile(img, cam, H, p_from, p_to, step_px=0.35):
    """Sample along the image-space segment joining two plane points."""
    u0, v0 = plane_to_distorted_px(cam, H, p_from[0], p_from[1])
    u1, v1 = plane_to_distorted_px(cam, H, p_to[0], p_to[1])
    length = math.hypot(u1 - u0, v1 - v0)
    n = max(8, int(length / step_px))
    out = []
    for i in range(n + 1):
        f = i / n
        u = u0 + (u1 - u0) * f
        v = v0 + (v1 - v0) * f
        if not img.inside(u, v, 1.0):
            raise MeasureError("SEGMENTATION_OUT_OF_IMAGE")
        out.append((u, v, img.bilinear(u, v)))
    return out


def _crossings(profile, level):
    """All subpixel crossings of `level`; returns list of (index_float,u,v)."""
    out = []
    for i in range(1, len(profile)):
        a = profile[i - 1][2]
        b = profile[i][2]
        if (a - level) * (b - level) <= 0.0 and a != b:
            f = (level - a) / (b - a)
            u = profile[i - 1][0] + (profile[i][0] - profile[i - 1][0]) * f
            v = profile[i - 1][1] + (profile[i][1] - profile[i - 1][1]) * f
            out.append((i - 1 + f, u, v))
    return out


def _select_cluster(points, shape_class, apex_frac, want_max):
    """Choose the edge points that define the extreme.

    This is part of the *measurand definition*, not of the noise model: for a
    glyph such as `H` or `T` only the scanlines that reach the true extreme (the
    stems) may contribute, and scanlines that terminate on a crossbar must be
    excluded.  Keeping selection outside the bootstrap is essential -- resampling
    the selection itself makes the standard error meaningless (it flips between
    two structurally different edges).
    """
    if len(points) < 4:
        raise MeasureError("SEGMENTATION_TOO_FEW_POINTS")
    ns = [p[1] for p in points]
    if shape_class == "FLAT_TOP":
        spread = max(ns) - min(ns)
        tol = max(0.15 * spread, 3.0 * max(mad_sigma(ns), 1e-6))
        if want_max:
            ref = max(ns)
            sel = [p for p in points if ref - p[1] <= tol]
        else:
            ref = min(ns)
            sel = [p for p in points if p[1] - ref <= tol]
    else:
        ref_idx = max(range(len(points)), key=lambda i: ns[i] if want_max else -ns[i])
        t_apex = points[ref_idx][0]
        ts = [p[0] for p in points]
        half = 0.5 * (max(ts) - min(ts)) * apex_frac
        sel = [p for p in points if abs(p[0] - t_apex) <= max(half, 1e-6)]
    if len(sel) < 4:
        sel = list(points)
    return sel


def _fit_residual(sel, shape_class):
    """RMS residual of the fitted edge model, in plane millimetres.

    A ragged boundary (dither, halftone, broken print) shows up here even when
    the resulting height happens to look plausible, so this is gated.
    """
    if len(sel) < 4:
        return float("nan")
    ts = [p[0] for p in sel]
    ns = [p[1] for p in sel]
    try:
        if shape_class == "FLAT_TOP":
            _, _, rms = fit_line_tls(sel)
            return rms
        c = polyfit(ts, ns, 2)
        res = [ns[i] - polyval(c, ts[i]) for i in range(len(ts))]
        return math.sqrt(sum(r * r for r in res) / len(res))
    except Exception:
        return float("nan")


def _fit_on(sel, shape_class, want_max):
    """Fit the edge model to an already selected cluster and return its extreme."""
    if len(sel) < 3:
        raise MeasureError("SEGMENTATION_TOO_FEW_POINTS")
    ns = [p[1] for p in sel]
    if shape_class == "FLAT_TOP":
        (mx, my), (vx, vy), _ = fit_line_tls(sel)
        tc = mean([p[0] for p in sel])
        if abs(vx) < 1e-9:
            return my
        return my + vy / vx * (tc - mx)
    if len(sel) < 4:
        return max(ns) if want_max else min(ns)
    c = polyfit([p[0] for p in sel], [p[1] for p in sel], 2)
    a2, a1, a0 = c[2], c[1], c[0]
    if abs(a2) < 1e-12:
        return max(ns) if want_max else min(ns)
    tv = -a1 / (2.0 * a2)
    if tv < min(p[0] for p in sel) or tv > max(p[0] for p in sel):
        return max(ns) if want_max else min(ns)
    return a0 + a1 * tv + a2 * tv * tv


def _fit_extreme(points, shape_class, apex_frac, want_max):
    sel = _select_cluster(points, shape_class, apex_frac, want_max)
    return _fit_on(sel, shape_class, want_max), len(sel)


def _bootstrap_extreme(points, shape_class, rng, n_boot=160, apex_frac=0.35,
                       want_max=True):
    """Standard error of the fitted extreme, bootstrapped *within* the cluster."""
    sel = _select_cluster(points, shape_class, apex_frac, want_max)
    n = len(sel)
    if n < 4:
        return float("nan"), n
    vals = []
    for _ in range(n_boot):
        samp = [sel[rng.randint(n)] for _ in range(n)]
        try:
            vals.append(_fit_on(samp, shape_class, want_max))
        except Exception:
            continue
    if len(vals) < 20:
        return float("nan"), n
    return sd(vals), n


def measure_glyph(img, cam, H, Hinv, roi_mm, shape_class, policy, rng=None,
                  baseline_dir=(1.0, 0.0)):
    """Measure one glyph.  `roi_mm` = (cx, cy, w, h) in plane millimetres."""
    if rng is None:
        rng = Rng(12345)
    cx, cy, w, h = roi_mm
    n_scan = int(policy["scanlines"])
    frac = float(policy["boundary_fraction"])
    sens = [float(f) for f in policy["sensitivity_fractions"]]

    bx, by = baseline_dir
    bl = math.hypot(bx, by) or 1.0
    bx, by = bx / bl, by / bl
    nx, ny = -by, bx                      # baseline normal, "up" in plane

    half_t = 0.5 * w * 0.80               # skip the outer 10% each side
    span_n = 0.5 * h * 1.45               # scan beyond the glyph

    profiles = []
    for i in range(n_scan):
        f = -1.0 + 2.0 * i / max(1, n_scan - 1)
        t = f * half_t
        base = (cx + bx * t, cy + by * t)
        p_top = (base[0] + nx * span_n, base[1] + ny * span_n)
        p_bot = (base[0] - nx * span_n, base[1] - ny * span_n)
        profiles.append((t, _sample_profile(img, cam, H, p_top, p_bot)))

    all_vals = [s[2] for _, pr in profiles for s in pr]
    paper_g = percentile(all_vals, 0.90)
    ink_g = percentile(all_vals, 0.05)
    if paper_g - ink_g < 1e-6:
        raise MeasureError("SEGMENTATION_NO_CONTRAST")

    edges = {f: {"top": [], "bot": []} for f in [frac] + sens}
    crossing_counts = []
    rise_mm = []
    overshoot = []
    noise_samples = []
    used = 0

    for t, pr in profiles:
        vals = [s[2] for s in pr]
        k = max(3, len(vals) // 8)
        outer = vals[:k] + vals[-k:]
        paper_l = median(outer)
        noise_samples.append(sd(outer))
        dark = [v for v in vals if v < 0.5 * (paper_l + ink_g)]
        ink_l = median(dark) if len(dark) >= 3 else ink_g
        if paper_l - ink_l < 0.02:
            continue
        cr_main = _crossings(pr, ink_l + frac * (paper_l - ink_l))
        if len(cr_main) < 2:
            continue
        crossing_counts.append(len(cr_main))
        ok = True
        for f in [frac] + sens:
            cr = _crossings(pr, ink_l + f * (paper_l - ink_l))
            if len(cr) < 2:
                ok = False
                break
            for key, c in (("top", cr[0]), ("bot", cr[-1])):
                X, Y = distorted_px_to_plane(cam, Hinv, c[1], c[2])
                edges[f][key].append((t, (X - cx) * nx + (Y - cy) * ny))
        if not ok:
            continue
        used += 1
        # 10-90 rise distance of the leading (top) edge, in plane mm
        c10 = _crossings(pr, ink_l + 0.10 * (paper_l - ink_l))
        c90 = _crossings(pr, ink_l + 0.90 * (paper_l - ink_l))
        if c10 and c90:
            p10 = distorted_px_to_plane(cam, Hinv, c10[0][1], c10[0][2])
            p90 = distorted_px_to_plane(cam, Hinv, c90[0][1], c90[0][2])
            rise_mm.append(abs((p90[0] - p10[0]) * nx + (p90[1] - p10[1]) * ny))
        first = cr_main[0][0]
        pre = [v for idx, v in enumerate(vals) if idx < first - 2]
        if pre:
            overshoot.append(max(0.0, max(pre) - paper_l) / max(paper_l - ink_l, 1e-9))

    if used < max(6, n_scan // 4):
        raise MeasureError("SEGMENTATION_INSUFFICIENT_SCANLINES",
                           "used=%d of %d" % (used, n_scan))

    apex = float(policy["apex_fit_window_frac"])
    heights = {}
    cluster_sizes = {}
    for f in [frac] + sens:
        top, n_top_sel = _fit_extreme(edges[f]["top"], shape_class, apex, True)
        bot, n_bot_sel = _fit_extreme(edges[f]["bot"], shape_class, apex, False)
        heights[f] = top - bot
        cluster_sizes[f] = (n_top_sel, n_bot_sel)

    top_sel = _select_cluster(edges[frac]["top"], shape_class, apex, True)
    bot_sel = _select_cluster(edges[frac]["bot"], shape_class, apex, False)
    fit_rms = max(_fit_residual(top_sel, shape_class),
                  _fit_residual(bot_sel, shape_class))

    se_top, n_top_sel = _bootstrap_extreme(edges[frac]["top"], shape_class, rng,
                                           apex_frac=apex, want_max=True)
    se_bot, n_bot_sel = _bootstrap_extreme(edges[frac]["bot"], shape_class, rng,
                                           apex_frac=apex, want_max=False)
    u_edge = math.sqrt((se_top if se_top == se_top else 0.0) ** 2 +
                       (se_bot if se_bot == se_bot else 0.0) ** 2)

    tops = [p[1] for p in edges[frac]["top"]]
    bots = [p[1] for p in edges[frac]["bot"]]
    h_maxmin = max(tops) - min(bots)

    rise = median(rise_mm) if rise_mm else float("nan")
    noise = median([v for v in noise_samples if v == v]) if noise_samples else 0.0
    contrast = ((paper_g - ink_g) / (paper_g + ink_g)) if (paper_g + ink_g) > 0 else 0.0

    return {
        "h_mm": heights[frac],
        "h_mm_sensitivity": {("%.2f" % f): heights[f] for f in sens},
        "h_mm_maxminus_min_diagnostic": h_maxmin,
        "u_edge_mm": u_edge,
        "scanlines_used": used,
        "scanlines_requested": n_scan,
        "crossings_median": median(crossing_counts) if crossing_counts else 0,
        "edge_rise_1090_mm": rise,
        "edge_sigma_mm": (rise / 2.563) if rise == rise else float("nan"),
        "overshoot_ratio": max(overshoot) if overshoot else 0.0,
        "paper_level": paper_g,
        "ink_level": ink_g,
        "michelson_contrast": contrast,
        "noise_sigma": noise,
        "snr": ((paper_g - ink_g) / noise) if noise > 1e-9 else float("inf"),
        "n_top_points": len(edges[frac]["top"]),
        "n_bot_points": len(edges[frac]["bot"]),
        "edge_fit_rms_mm": fit_rms,
        "n_top_cluster": n_top_sel,
        "n_bot_cluster": n_bot_sel,
        "cluster_sizes_by_fraction": {("%.2f" % f): list(v)
                                      for f, v in cluster_sizes.items()},
    }


def clipping_stats(img, cam, H, roi_mm):
    """Fraction of clipped samples in a plane-space rectangle."""
    cx, cy, w, h = roi_mm
    lo = hi = tot = 0
    steps = 24
    for i in range(steps):
        for j in range(steps):
            x = cx + w * (i / (steps - 1.0) - 0.5) * 1.4
            y = cy + h * (j / (steps - 1.0) - 0.5) * 1.6
            u, v = plane_to_distorted_px(cam, H, x, y)
            if not img.inside(u, v, 1.0):
                continue
            val = img.bilinear(u, v)
            tot += 1
            if val <= 1e-4:
                lo += 1
            elif val >= 1.0 - 1e-4:
                hi += 1
    if tot == 0:
        return {"clip_dark_frac": 1.0, "clip_bright_frac": 1.0, "samples": 0}
    return {"clip_dark_frac": lo / tot, "clip_bright_frac": hi / tot, "samples": tot}


def estimate_baseline_dir(img, cam, H, Hinv, roi_mm, policy):
    """Refine the baseline direction from the glyph's bottom edge points."""
    cx, cy, w, h = roi_mm
    n_scan = max(8, int(policy["scanlines"]) // 2)
    pts = []
    for i in range(n_scan):
        f = -1.0 + 2.0 * i / max(1, n_scan - 1)
        t = f * 0.5 * w * 0.8
        try:
            pr = _sample_profile(img, cam, H, (cx + t, cy + 0.75 * h),
                                 (cx + t, cy - 0.75 * h))
        except MeasureError:
            continue
        vals = [s[2] for s in pr]
        k = max(3, len(vals) // 8)
        paper_l = median(vals[:k] + vals[-k:])
        ink_l = min(vals)
        if paper_l - ink_l < 0.02:
            continue
        cr = _crossings(pr, 0.5 * (paper_l + ink_l))
        if len(cr) < 2:
            continue
        X, Y = distorted_px_to_plane(cam, Hinv, cr[-1][1], cr[-1][2])
        pts.append((X, Y))
    if len(pts) < 5:
        return (1.0, 0.0), float("nan")
    _, (vx, vy), rms = fit_line_tls(pts)
    if vx < 0:
        vx, vy = -vx, -vy
    ang = math.degrees(math.atan2(vy, vx))
    if abs(ang) > 20.0:                 # implausible for a controlled capture
        return (1.0, 0.0), float("nan")
    return (vx, vy), ang
