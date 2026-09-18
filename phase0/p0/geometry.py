"""Homography estimation from control points, plus geometric diagnostics.

`fit_homography` expects **ideal (undistorted) pixel** coordinates so that lens
distortion is removed before the projective fit, exactly as the pipeline spec
requires.  Estimation is normalised DLT followed by Gauss-Newton refinement of
the image-space reprojection error.
"""
from __future__ import annotations

import math

from .camera import rho_at
from .core import lstsq, mat3_mul, solve


def _normalise(pts):
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    d = sum(math.hypot(p[0] - mx, p[1] - my) for p in pts) / n
    s = math.sqrt(2.0) / d if d > 1e-12 else 1.0
    T = [[s, 0.0, -s * mx], [0.0, s, -s * my], [0.0, 0.0, 1.0]]
    out = [((p[0] - mx) * s, (p[1] - my) * s) for p in pts]
    return out, T


def _inv_affine(T):
    s = T[0][0]
    tx = T[0][2]
    ty = T[1][2]
    return [[1.0 / s, 0.0, -tx / s], [0.0, 1.0 / s, -ty / s], [0.0, 0.0, 1.0]]


def _dlt(src, dst):
    rows = []
    rhs = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y])
        rhs.append(u)
        rows.append([0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y])
        rhs.append(v)
    h = lstsq(rows, rhs)
    return [[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1.0]]


def _refine(H, src, dst, iters=12):
    h = [H[0][0], H[0][1], H[0][2], H[1][0], H[1][1], H[1][2], H[2][0], H[2][1]]
    prev_cost = None
    for _ in range(iters):
        ATA = [[0.0] * 8 for _ in range(8)]
        ATb = [0.0] * 8
        cost = 0.0
        for (x, y), (u_o, v_o) in zip(src, dst):
            w = h[6] * x + h[7] * y + 1.0
            if abs(w) < 1e-12:
                return H
            u = (h[0] * x + h[1] * y + h[2]) / w
            v = (h[3] * x + h[4] * y + h[5]) / w
            ru = u_o - u
            rv = v_o - v
            cost += ru * ru + rv * rv
            ju = [x / w, y / w, 1.0 / w, 0.0, 0.0, 0.0, -u * x / w, -u * y / w]
            jv = [0.0, 0.0, 0.0, x / w, y / w, 1.0 / w, -v * x / w, -v * y / w]
            for a in range(8):
                if ju[a]:
                    ATb[a] += ju[a] * ru
                if jv[a]:
                    ATb[a] += jv[a] * rv
                for b in range(a, 8):
                    ATA[a][b] += ju[a] * ju[b] + jv[a] * jv[b]
        for a in range(8):
            for b in range(a):
                ATA[a][b] = ATA[b][a]
            ATA[a][a] += 1e-12
        try:
            dh = solve(ATA, ATb)
        except ZeroDivisionError:
            break
        h = [h[i] + dh[i] for i in range(8)]
        if prev_cost is not None and abs(prev_cost - cost) < 1e-14 * max(1.0, cost):
            break
        prev_cost = cost
    return [[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1.0]]


def fit_homography(plane_pts, img_pts):
    """plane(mm) -> ideal pixel homography."""
    if len(plane_pts) < 4:
        raise ValueError("need >= 4 control points")
    sn, Ts = _normalise(plane_pts)
    dn, Td = _normalise(img_pts)
    Hn = _dlt(sn, dn)
    Hn = _refine(Hn, sn, dn)
    H = mat3_mul(_inv_affine(Td), mat3_mul(Hn, Ts))
    H = _refine(H, plane_pts, img_pts)
    if abs(H[2][2]) > 1e-12:
        H = [[c / H[2][2] for c in row] for row in H]
    return H


def reprojection_stats(H, plane_pts, img_pts):
    res = []
    for (x, y), (u_o, v_o) in zip(plane_pts, img_pts):
        w = H[2][0] * x + H[2][1] * y + H[2][2]
        u = (H[0][0] * x + H[0][1] * y + H[0][2]) / w
        v = (H[1][0] * x + H[1][1] * y + H[1][2]) / w
        res.append(math.hypot(u - u_o, v - v_o))
    n = len(res)
    return {"rms_px": math.sqrt(sum(r * r for r in res) / n),
            "max_px": max(res),
            "n_points": n,
            "residuals_px": res}


def leave_one_group_out_scale(plane_pts, img_pts, groups, at_mm):
    """Relative spread of local scale when each control-point group is dropped."""
    gids = sorted(set(groups))
    rhos = []
    per_group = {}
    for g in gids:
        pp = [p for p, gg in zip(plane_pts, groups) if gg != g]
        ip = [p for p, gg in zip(img_pts, groups) if gg != g]
        if len(pp) < 4:
            continue
        try:
            Hg = fit_homography(pp, ip)
        except Exception:
            continue
        rho, _, _ = rho_at(Hg, at_mm[0], at_mm[1])
        if rho > 0:
            rhos.append(rho)
            per_group[str(g)] = rho
    if len(rhos) < 2:
        return {"rel_spread": float("nan"), "n_fits": len(rhos), "per_group": per_group}
    m = sum(rhos) / len(rhos)
    return {"rel_spread": (max(rhos) - min(rhos)) / m, "n_fits": len(rhos),
            "per_group": per_group}


def point_in_hull(pt, pts, margin_mm=0.0):
    """Convex-hull containment test with an inward margin."""
    hull = _convex_hull(pts)
    n = len(hull)
    if n < 3:
        return False
    cx = sum(p[0] for p in hull) / n
    cy = sum(p[1] for p in hull) / n
    for i in range(n):
        x1, y1 = hull[i]
        x2, y2 = hull[(i + 1) % n]
        ex, ey = x2 - x1, y2 - y1
        ln = math.hypot(ex, ey) or 1.0
        nx, ny = -ey / ln, ex / ln
        # outward normal
        if (x1 - cx) * nx + (y1 - cy) * ny < 0:
            nx, ny = -nx, -ny
        if (pt[0] - x1) * nx + (pt[1] - y1) * ny > -margin_mm:
            return False
    return True


def hull_margin_mm(pt, pts):
    """Signed distance from `pt` to the hull boundary (positive = inside)."""
    hull = _convex_hull(pts)
    n = len(hull)
    if n < 3:
        return float("-inf")
    cx = sum(p[0] for p in hull) / n
    cy = sum(p[1] for p in hull) / n
    best = float("inf")
    for i in range(n):
        x1, y1 = hull[i]
        x2, y2 = hull[(i + 1) % n]
        ex, ey = x2 - x1, y2 - y1
        ln = math.hypot(ex, ey) or 1.0
        nx, ny = -ey / ln, ex / ln
        if (x1 - cx) * nx + (y1 - cy) * ny < 0:
            nx, ny = -nx, -ny
        best = min(best, -((pt[0] - x1) * nx + (pt[1] - y1) * ny))
    return best


def _convex_hull(points):
    pts = sorted(set((float(p[0]), float(p[1])) for p in points))
    if len(pts) < 3:
        return pts

    def half(seq):
        st = []
        for p in seq:
            while len(st) >= 2:
                (x1, y1), (x2, y2) = st[-2], st[-1]
                if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) > 0:
                    break
                st.pop()
            st.append(p)
        return st

    lower = half(pts)
    upper = half(list(reversed(pts)))
    return lower[:-1] + upper[:-1]
