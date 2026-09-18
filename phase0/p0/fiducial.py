"""NDFID-1 fiducial: coded square markers, rendering bits and detection.

Why a custom marker instead of ArUco
------------------------------------
cv2.aruco is unavailable in this sandbox (no network, see A-01).  NDFID-1 keeps
the *metrological* design that matters and that the review recommended:

* control points come from intersecting **edge lines** fitted to long straight
  marker borders, not from a corner detector applied to a quad.  Edge-line
  intersection is better conditioned than corner search.
* four markers surround the region of interest so the measured area is always
  interpolated inside the control-point hull.
* marker identity is coded, so a wrong or partial frame is rejected rather than
  silently measured.

`detect_frame()` returns a detector-agnostic `ControlPoints` object, so swapping
in cv2.aruco / cv2.aruco.CharucoDetector later only changes this module.

Marker layout (6 x 6 cells, cell = side/6):
    row 0 and row 5, col 0 and col 5 : black border ring
    inner 4 x 4                      : white, with 4 code cells at the
                                       positions (1,1) (1,4) (4,1) (4,4)... no:
    inner 4 x 4 cells carry a 16-bit code; cell black = 1.
"""
from __future__ import annotations

import math

from .core import fit_line_tls, median, percentile

CELLS = 6            # total cells per side (1 cell border on each side)
CODE_CELLS = 4       # inner code grid is 4 x 4


# --------------------------------------------------------------------------
# dictionary
# --------------------------------------------------------------------------


def _rot90(bits):
    """Rotate a 4x4 bit list (row major) by 90 degrees clockwise."""
    n = CODE_CELLS
    return [bits[(n - 1 - c) * n + r] for r in range(n) for c in range(n)]


def _hamming(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


def _build_dictionary(size=8, min_dist=6):
    """Deterministic greedy dictionary with rotation-aware Hamming distance."""
    entries = []
    for code in range(1 << (CODE_CELLS * CODE_CELLS)):
        bits = [(code >> i) & 1 for i in range(CODE_CELLS * CODE_CELLS)]
        s = sum(bits)
        if s < 5 or s > 11:              # avoid near-empty / near-full markers
            continue
        rots = [bits]
        for _ in range(3):
            rots.append(_rot90(rots[-1]))
        # reject self-symmetric codes: orientation must be recoverable
        if any(_hamming(rots[0], r) < min_dist for r in rots[1:]):
            continue
        ok = True
        for _, other_rots in entries:
            for r in rots:
                for o in other_rots:
                    if _hamming(r, o) < min_dist:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            entries.append((bits, rots))
            if len(entries) >= size:
                break
    return [e[0] for e in entries]


DICTIONARY = _build_dictionary()


def marker_bit_grid(marker_id: int):
    """Full CELLS x CELLS grid, True = black."""
    code = DICTIONARY[marker_id]
    grid = [[True] * CELLS for _ in range(CELLS)]
    for r in range(CODE_CELLS):
        for c in range(CODE_CELLS):
            grid[r + 1][c + 1] = bool(code[r * CODE_CELLS + c])
    return grid


def ink_at_marker(marker_id: int, fx: float, fy: float) -> bool:
    """fx, fy in [0,1] relative to the marker square (fy measured downwards)."""
    if fx < 0.0 or fx >= 1.0 or fy < 0.0 or fy >= 1.0:
        return False
    grid = marker_bit_grid(marker_id)
    c = int(fx * CELLS)
    r = int(fy * CELLS)
    return grid[r][c]


# --------------------------------------------------------------------------
# detection
# --------------------------------------------------------------------------


class ControlPoints:
    """Detector-agnostic result: matched plane <-> image control points."""

    __slots__ = ("plane", "image", "groups", "marker_ids", "diagnostics")

    def __init__(self, plane, image, groups, marker_ids, diagnostics):
        self.plane = plane            # [(X_mm, Y_mm), ...]
        self.image = image            # [(u_px, v_px), ...] distorted pixels
        self.groups = groups          # [group_index_per_point]
        self.marker_ids = marker_ids
        self.diagnostics = diagnostics


class DetectError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code + (": " + detail if detail else ""))
        self.code = code
        self.detail = detail


def _components(mask, w, h, min_area):
    """4-connected labelling of a boolean mask; returns list of pixel lists."""
    seen = bytearray(w * h)
    out = []
    for start in range(w * h):
        if mask[start] and not seen[start]:
            stack = [start]
            seen[start] = 1
            comp = []
            while stack:
                p = stack.pop()
                comp.append(p)
                y, x = divmod(p, w)
                if x > 0 and mask[p - 1] and not seen[p - 1]:
                    seen[p - 1] = 1
                    stack.append(p - 1)
                if x < w - 1 and mask[p + 1] and not seen[p + 1]:
                    seen[p + 1] = 1
                    stack.append(p + 1)
                if y > 0 and mask[p - w] and not seen[p - w]:
                    seen[p - w] = 1
                    stack.append(p - w)
                if y < h - 1 and mask[p + w] and not seen[p + w]:
                    seen[p + w] = 1
                    stack.append(p + w)
            if len(comp) >= min_area:
                out.append(comp)
    return out


def _hull(points):
    pts = sorted(set(points))
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
    upper = half(reversed(pts))
    return lower[:-1] + upper[:-1]


def _quad_from_hull(hull):
    """Pick 4 hull vertices maximising enclosed area (rotating search)."""
    n = len(hull)
    if n < 4:
        return None
    if n > 40:                      # decimate for speed, keeps shape
        step = n / 40.0
        hull = [hull[int(i * step)] for i in range(40)]
        n = len(hull)

    def area(a, b, c, d):
        pts = [hull[a], hull[b], hull[c], hull[d]]
        s = 0.0
        for i in range(4):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % 4]
            s += x1 * y2 - x2 * y1
        return abs(s) * 0.5

    best = None
    best_a = -1.0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                for l in range(k + 1, n):
                    a = area(i, j, k, l)
                    if a > best_a:
                        best_a = a
                        best = (i, j, k, l)
    if best is None:
        return None
    return [hull[i] for i in best], best_a


def _refine_edges(img, quad, search_px, samples_per_edge, thr_level,
                  lvl10=None, lvl90=None):
    """Fit a subpixel line to each quad edge; return the 4 corner intersections.

    For every sample position along an edge we walk perpendicular to it and
    locate the `thr_level` crossing of the linear luminance profile with
    subpixel linear interpolation.  Each edge is then a total-least-squares line
    fit through those points, and corners are line intersections.
    """
    lines = []
    edge_rms = []
    rises = []
    nq = len(quad)
    cx = sum(p[0] for p in quad) / nq
    cy = sum(p[1] for p in quad) / nq
    step = 0.25
    for e in range(4):
        x1, y1 = quad[e]
        x2, y2 = quad[(e + 1) % 4]
        ex, ey = x2 - x1, y2 - y1
        elen = math.hypot(ex, ey)
        if elen < 4.0:
            raise DetectError("FIDUCIAL_EDGE_TOO_SHORT")
        ex, ey = ex / elen, ey / elen
        nx, ny = -ey, ex
        # make the normal point away from the marker centre
        mx, my = 0.5 * (x1 + x2), 0.5 * (y1 + y2)
        if (mx - cx) * nx + (my - cy) * ny < 0:
            nx, ny = -nx, -ny
        pts = []
        for s in range(samples_per_edge):
            f = 0.15 + 0.7 * s / max(1, samples_per_edge - 1)
            px = x1 + ex * elen * f
            py = y1 + ey * elen * f
            # Sample the whole profile once, then use *locally* estimated ink and
            # paper levels.  A single global threshold biases the edge position
            # wherever illumination is uneven, which silently corrupts the
            # homography (observed in run v1, fixture E_ILLUM-gradient).
            n_steps = int(2 * search_px / step)
            prof = []
            for i in range(n_steps + 1):
                t = -search_px + step * i
                prof.append((t, img.bilinear(px + nx * t, py + ny * t)))
            k = max(2, len(prof) // 4)
            ink_l = median([v for _, v in prof[:k]])
            paper_l = median([v for _, v in prof[-k:]])
            if paper_l - ink_l < 0.03:
                continue
            lv50 = 0.5 * (ink_l + paper_l)
            hit = _cross_in_profile(prof, lv50)
            if hit is not None:
                pts.append((px + nx * hit, py + ny * hit))
            if lvl10 is not None:
                t10 = _cross_in_profile(prof, ink_l + 0.10 * (paper_l - ink_l))
                t90 = _cross_in_profile(prof, ink_l + 0.90 * (paper_l - ink_l))
                if t10 is not None and t90 is not None:
                    rises.append(abs(t10 - t90))
        if len(pts) < 5:
            raise DetectError("FIDUCIAL_EDGE_FIT_FAILED")
        p0, d, rms = fit_line_tls(pts)
        lines.append((p0, d))
        edge_rms.append(rms)

    corners = []
    for e in range(4):
        (p1, d1) = lines[e]
        (p2, d2) = lines[(e + 1) % 4]
        den = d1[0] * (-d2[1]) - d1[1] * (-d2[0])
        if abs(den) < 1e-9:
            raise DetectError("FIDUCIAL_EDGE_PARALLEL")
        bx = p2[0] - p1[0]
        by = p2[1] - p1[1]
        s = (bx * (-d2[1]) - by * (-d2[0])) / den
        corners.append((p1[0] + d1[0] * s, p1[1] + d1[1] * s))
    return corners, edge_rms, rises



def _cross_in_profile(prof, level):
    """First subpixel crossing of `level` in a sampled (t, value) profile."""
    for i in range(1, len(prof)):
        t0, a = prof[i - 1]
        t1, b = prof[i]
        if (a - level) * (b - level) <= 0.0 and a != b:
            return t0 + (t1 - t0) * ((level - a) / (b - a))
    return None

def _homography_from_quad(src, dst):
    """Minimal 4-point homography src->dst (unit square style), plain DLT."""
    from .core import lstsq
    rows = []
    rhs = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        rhs.append(u)
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        rhs.append(v)
    h = lstsq(rows, rhs)
    return [[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1.0]]


def _read_code(img, corners, thr_level):
    """Sample the 4x4 code grid; returns bits (row major) or None."""
    from .core import apply_h
    H = _homography_from_quad([(0, 0), (1, 0), (1, 1), (0, 1)], corners)
    bits = []
    for r in range(CODE_CELLS):
        for c in range(CODE_CELLS):
            fx = (c + 1.5) / CELLS
            fy = (r + 1.5) / CELLS
            vals = []
            for dx, dy in ((0.0, 0.0), (0.2, 0.0), (-0.2, 0.0), (0.0, 0.2), (0.0, -0.2)):
                u, v = apply_h(H, fx + dx / CELLS, fy + dy / CELLS)
                vals.append(img.bilinear(u, v))
            bits.append(1 if median(vals) < thr_level else 0)
    return bits


def _match_code(bits):
    """Return (marker_id, rotation) or None.  rotation counts 90 deg CW steps."""
    for mid, code in enumerate(DICTIONARY):
        rot = list(code)
        for k in range(4):
            if rot == bits:
                return mid, k
            rot = _rot90(rot)
    return None


def detect_frame(img, frame_cert, params=None):
    """Detect the four coded markers and build matched control points."""
    p = {"min_marker_px": 24, "sample_per_edge": 24, "search_px": 6.0,
         "max_components": 400}
    if params:
        p.update(params)

    w, h = img.w, img.h
    # Markers cover only a few percent of the canvas, so the dark level must be
    # taken from a low quantile rather than a symmetric one.
    vals = [img.lin[i] for i in range(0, w * h, max(1, (w * h) // 40000))]
    paper = percentile(vals, 0.90)
    ink = percentile(vals, 0.001)
    if paper - ink < 0.05:
        raise DetectError("FIDUCIAL_NO_CONTRAST",
                          "paper=%.3f ink=%.3f" % (paper, ink))
    thr = 0.5 * (paper + ink)

    mask = bytearray(w * h)
    lin = img.lin
    for i in range(w * h):
        if lin[i] < thr:
            mask[i] = 1
    min_area = p["min_marker_px"] * p["min_marker_px"] // 3
    comps = _components(mask, w, h, min_area)
    if len(comps) > p["max_components"]:
        comps = sorted(comps, key=len, reverse=True)[:p["max_components"]]

    found = {}
    diag = {"components": len(comps), "edge_rms_px": [], "edge_rise_px": [],
            "reject": {}}
    for comp in comps:
        xs = [c % w for c in comp]
        ys = [c // w for c in comp]
        bw = max(xs) - min(xs) + 1
        bh = max(ys) - min(ys) + 1
        if bw < p["min_marker_px"] or bh < p["min_marker_px"]:
            continue
        if not (0.4 < bw / float(bh) < 2.5):
            diag["reject"]["aspect"] = diag["reject"].get("aspect", 0) + 1
            continue
        # ring shaped: the dark border must enclose brighter interior
        fill = len(comp) / float(bw * bh)
        if fill > 0.92:
            diag["reject"]["solid"] = diag["reject"].get("solid", 0) + 1
            continue
        hull = _hull(list(zip(xs, ys)))
        q = _quad_from_hull(hull)
        if not q:
            continue
        quad, qarea = q
        if qarea < 0.45 * bw * bh:
            diag["reject"]["not_quad"] = diag["reject"].get("not_quad", 0) + 1
            continue
        # order the quad counter clockwise in image coordinates
        cxm = sum(pt[0] for pt in quad) / 4.0
        cym = sum(pt[1] for pt in quad) / 4.0
        quad = sorted(quad, key=lambda pt: math.atan2(pt[1] - cym, pt[0] - cxm))
        try:
            corners, erms, rises = _refine_edges(
                img, quad, p["search_px"], p["sample_per_edge"], thr,
                ink + 0.10 * (paper - ink), ink + 0.90 * (paper - ink))
        except DetectError:
            diag["reject"]["edge_fit"] = diag["reject"].get("edge_fit", 0) + 1
            continue
        bits = _read_code(img, corners, thr)
        m = _match_code(bits)
        if m is None:
            diag["reject"]["code"] = diag["reject"].get("code", 0) + 1
            continue
        mid, _rot = m
        if mid in found:
            raise DetectError("FIDUCIAL_DUPLICATE_ID", "id=%d" % mid)
        found[mid] = corners
        diag["edge_rms_px"].append(max(erms))
        if rises:
            diag.setdefault("edge_rise_px", []).extend(rises)

    expected = list(frame_cert["expected_marker_ids"])
    missing = [m for m in expected if m not in found]
    extra = [m for m in found if m not in expected]
    if missing:
        raise DetectError("FIDUCIAL_MISSING_MARKER", "missing=%s" % missing)
    if extra:
        raise DetectError("FIDUCIAL_UNEXPECTED_MARKER", "extra=%s" % extra)

    # Correspondence is established geometrically, not from the code rotation:
    # marker centres are rotation invariant, so an initial 4 point homography
    # from surveyed centres lets every surveyed corner be matched to its nearest
    # detected corner.  This keeps the detector independent of marker encoding.
    survey = frame_cert["markers"]
    for mid in expected:
        if str(mid) not in survey:
            raise DetectError("FIDUCIAL_CERT_INCOMPLETE", "id=%d" % mid)
    src = []
    dst = []
    for mid in expected:
        cs = survey[str(mid)]["corners_mm"]
        src.append((sum(c[0] for c in cs) / 4.0, sum(c[1] for c in cs) / 4.0))
        pc = found[mid]
        dst.append((sum(p[0] for p in pc) / 4.0, sum(p[1] for p in pc) / 4.0))
    try:
        H0 = _homography_from_quad(src, dst)
    except ZeroDivisionError:
        raise DetectError("FIDUCIAL_DEGENERATE_LAYOUT")

    from .core import apply_h
    plane, image, groups = [], [], []
    max_match_px = 0.0
    for gi, mid in enumerate(expected):
        cs = survey[str(mid)]["corners_mm"]
        pc = list(found[mid])
        side_px = max(math.hypot(pc[i][0] - pc[(i + 1) % 4][0],
                                 pc[i][1] - pc[(i + 1) % 4][1]) for i in range(4))
        used = set()
        for (X, Y) in cs:
            pu, pv = apply_h(H0, float(X), float(Y))
            best = None
            best_d = 1e18
            for ci, (cu, cv) in enumerate(pc):
                if ci in used:
                    continue
                d = math.hypot(cu - pu, cv - pv)
                if d < best_d:
                    best_d = d
                    best = ci
            if best is None or best_d > 0.55 * side_px:
                raise DetectError("FIDUCIAL_CORNER_MATCH_FAILED",
                                  "id=%d d=%.1fpx" % (mid, best_d))
            used.add(best)
            max_match_px = max(max_match_px, best_d)
            plane.append((float(X), float(Y)))
            image.append(pc[best])
            groups.append(gi)
    diag["marker_count"] = len(found)
    diag["max_corner_match_px"] = max_match_px
    return ControlPoints(plane, image, groups, expected, diag)
