"""Minimal dependency-free SVG diagnostic plots.

matplotlib is unavailable in this sandbox (A-01), so the plots are emitted as
plain SVG.  They are intentionally simple: the numbers in the CSV are the
evidence, the plots only make the shape of the evidence visible.
"""
from __future__ import annotations

import math
import os

W, H = 720, 460
PAD_L, PAD_R, PAD_T, PAD_B = 78, 26, 44, 60
PALETTE = ["#1f5fa8", "#c0392b", "#148f56", "#8e44ad", "#d68910", "#16a085",
           "#7f8c8d", "#2c3e50"]


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _nice(lo, hi):
    if not (lo == lo and hi == hi):
        return 0.0, 1.0
    if hi - lo < 1e-12:
        c = 0.5 * (lo + hi)
        return c - 0.5, c + 0.5
    span = hi - lo
    return lo - 0.07 * span, hi + 0.07 * span


class Plot:
    def __init__(self, title, xlabel, ylabel, width=W, height=H):
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.w = width
        self.h = height
        self.series = []
        self.hlines = []
        self.vlines = []
        self.bands = []
        self.notes = []

    def scatter(self, xs, ys, label=None, color=None, radius=3.0):
        self.series.append(("scatter", list(xs), list(ys), label, color, radius))

    def line(self, xs, ys, label=None, color=None, width=2.0):
        self.series.append(("line", list(xs), list(ys), label, color, width))

    def errorbars(self, xs, los, his, label=None, color=None):
        self.series.append(("err", list(xs), list(zip(los, his)), label, color, 1.2))

    def bars(self, labels, values, label=None, color=None):
        self.series.append(("bars", list(labels), list(values), label, color, 0))

    def hline(self, y, label=None, color="#888", dash="4,3"):
        self.hlines.append((y, label, color, dash))

    def band(self, y0, y1, color="#e8f0fa"):
        self.bands.append((y0, y1, color))

    def note(self, text):
        self.notes.append(text)

    # ------------------------------------------------------------------
    def save(self, path):
        cat = any(s[0] == "bars" for s in self.series)
        xs_all, ys_all = [], []
        for kind, a, b, *_ in self.series:
            if kind == "bars":
                ys_all += [v for v in b if v == v]
                continue
            xs_all += [v for v in a if v == v]
            if kind == "err":
                for lo, hi in b:
                    if lo == lo:
                        ys_all.append(lo)
                    if hi == hi:
                        ys_all.append(hi)
            else:
                ys_all += [v for v in b if v == v]
        for y, _, _, _ in self.hlines:
            if y == y:
                ys_all.append(y)
        for y0, y1, _ in self.bands:
            ys_all += [y0, y1]
        if not ys_all:
            ys_all = [0.0, 1.0]
        if not xs_all:
            xs_all = [0.0, 1.0]
        x0, x1 = _nice(min(xs_all), max(xs_all))
        y0, y1 = _nice(min(ys_all), max(ys_all))

        pw = self.w - PAD_L - PAD_R
        ph = self.h - PAD_T - PAD_B

        def sx(v):
            if cat:
                return PAD_L + pw * v
            return PAD_L + pw * (v - x0) / (x1 - x0)

        def sy(v):
            return PAD_T + ph * (1.0 - (v - y0) / (y1 - y0))

        out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
               'viewBox="0 0 %d %d" font-family="DejaVu Sans,Arial,sans-serif">'
               % (self.w, self.h, self.w, self.h)]
        out.append('<rect width="100%" height="100%" fill="white"/>')
        out.append('<text x="%d" y="24" font-size="15" font-weight="bold">%s</text>'
                   % (PAD_L, _esc(self.title)))

        for by0, by1, color in self.bands:
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>'
                       % (PAD_L, sy(by1), pw, abs(sy(by0) - sy(by1)), color))

        # grid + y ticks
        for i in range(6):
            v = y0 + (y1 - y0) * i / 5.0
            yy = sy(v)
            out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#eee"/>'
                       % (PAD_L, yy, PAD_L + pw, yy))
            out.append('<text x="%.1f" y="%.1f" font-size="11" text-anchor="end" '
                       'fill="#444">%s</text>' % (PAD_L - 8, yy + 4, _fmtnum(v)))
        if not cat:
            for i in range(6):
                v = x0 + (x1 - x0) * i / 5.0
                xx = sx(v)
                out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#f4f4f4"/>'
                           % (xx, PAD_T, xx, PAD_T + ph))
                out.append('<text x="%.1f" y="%.1f" font-size="11" text-anchor="middle" '
                           'fill="#444">%s</text>' % (xx, PAD_T + ph + 18, _fmtnum(v)))

        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" '
                   'stroke="#999"/>' % (PAD_L, PAD_T, pw, ph))

        for y, label, color, dash in self.hlines:
            yy = sy(y)
            out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                       'stroke-dasharray="%s"/>' % (PAD_L, yy, PAD_L + pw, yy, color, dash))
            if label:
                out.append('<text x="%.1f" y="%.1f" font-size="10" fill="%s" '
                           'text-anchor="end">%s</text>'
                           % (PAD_L + pw - 4, yy - 4, color, _esc(label)))

        legend = []
        for si, (kind, a, b, label, color, size) in enumerate(self.series):
            col = color or PALETTE[si % len(PALETTE)]
            if label:
                legend.append((label, col))
            if kind == "scatter":
                for xv, yv in zip(a, b):
                    if xv != xv or yv != yv:
                        continue
                    out.append('<circle cx="%.2f" cy="%.2f" r="%.1f" fill="%s" '
                               'fill-opacity="0.75"/>' % (sx(xv), sy(yv), size, col))
            elif kind == "line":
                pts = ["%.2f,%.2f" % (sx(xv), sy(yv)) for xv, yv in zip(a, b)
                       if xv == xv and yv == yv]
                if pts:
                    out.append('<polyline points="%s" fill="none" stroke="%s" '
                               'stroke-width="%.1f"/>' % (" ".join(pts), col, size))
            elif kind == "err":
                for xv, (lo, hi) in zip(a, b):
                    if xv != xv or lo != lo or hi != hi:
                        continue
                    out.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" '
                               'stroke="%s" stroke-width="%.1f"/>'
                               % (sx(xv), sy(lo), sx(xv), sy(hi), col, size))
            elif kind == "bars":
                n = len(a)
                bw = pw / max(n, 1) * 0.6
                for i, (lab, val) in enumerate(zip(a, b)):
                    cx = PAD_L + pw * (i + 0.5) / n
                    top = sy(max(val, 0.0))
                    base = sy(0.0)
                    out.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" '
                               'fill="%s" fill-opacity="0.8"/>'
                               % (cx - bw / 2, min(top, base), bw, abs(base - top), col))
                    out.append('<text x="%.2f" y="%.2f" font-size="9.5" '
                               'text-anchor="end" fill="#333" '
                               'transform="rotate(-38 %.2f %.2f)">%s</text>'
                               % (cx, PAD_T + ph + 15, cx, PAD_T + ph + 15, _esc(lab)))
                    out.append('<text x="%.2f" y="%.2f" font-size="9.5" '
                               'text-anchor="middle" fill="#222">%s</text>'
                               % (cx, min(top, base) - 3, _fmtnum(val)))

        lx = PAD_L + 8
        ly = PAD_T + 14
        for label, col in legend:
            out.append('<rect x="%.1f" y="%.1f" width="9" height="9" fill="%s"/>'
                       % (lx, ly - 8, col))
            out.append('<text x="%.1f" y="%.1f" font-size="11" fill="#222">%s</text>'
                       % (lx + 13, ly, _esc(label)))
            ly += 15

        out.append('<text x="%.1f" y="%d" font-size="12" text-anchor="middle">%s</text>'
                   % (PAD_L + pw / 2, self.h - 20, _esc(self.xlabel)))
        out.append('<text x="16" y="%.1f" font-size="12" text-anchor="middle" '
                   'transform="rotate(-90 16 %.1f)">%s</text>'
                   % (PAD_T + ph / 2, PAD_T + ph / 2, _esc(self.ylabel)))
        for i, n in enumerate(self.notes):
            out.append('<text x="%d" y="%d" font-size="10" fill="#555">%s</text>'
                       % (PAD_L, self.h - 4 - 11 * (len(self.notes) - 1 - i), _esc(n)))
        out.append("</svg>")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out))
        return path


def _fmtnum(v):
    if v != v:
        return "nan"
    a = abs(v)
    if a >= 1000 or (a < 0.001 and a > 0):
        return "%.1e" % v
    if a >= 100:
        return "%.0f" % v
    if a >= 10:
        return "%.1f" % v
    if a >= 1:
        return "%.2f" % v
    return "%.3f" % v


def histogram(values, bins=18):
    vals = [v for v in values if v == v]
    if not vals:
        return [], []
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-12:
        hi = lo + 1e-9
    counts = [0] * bins
    for v in vals:
        k = int((v - lo) / (hi - lo) * bins)
        counts[min(k, bins - 1)] += 1
    centers = [lo + (hi - lo) * (i + 0.5) / bins for i in range(bins)]
    return centers, counts
