#!/usr/bin/env python3
"""Rasterise the deck layout to PNG for visual QA (stdlib only).

Shapes render in their real colours and geometry; text renders as greeked ink bars at
the exact measured line width, weight and colour. That is enough to inspect balance,
alignment, crowding, whitespace, colour and overlap -- which is what layout QA needs --
without a font rasteriser, which the sandbox does not have.
"""
from __future__ import annotations

import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_deck as bd                                    # noqa: E402
from deckkit import PAGE_H, PAGE_W, text_w                 # noqa: E402

S = 1.6                                    # scale: 960x540 -> 1536x864
W, H = int(PAGE_W * S), int(PAGE_H * S)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Canvas:
    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.px = bytearray(bg * w * h)

    def blend(self, x, y, col, a=1.0):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        i = (y * self.w + x) * 3
        if a >= 1.0:
            self.px[i:i + 3] = bytes(col)
        else:
            for k in range(3):
                self.px[i + k] = int(self.px[i + k] * (1 - a) + col[k] * a)

    def fill_rect(self, x, y, w, h, col, a=1.0):
        x0, y0 = int(round(x)), int(round(y))
        x1, y1 = int(round(x + w)), int(round(y + h))
        for yy in range(max(0, y0), min(self.h, max(y1, y0 + 1))):
            for xx in range(max(0, x0), min(self.w, max(x1, x0 + 1))):
                self.blend(xx, yy, col, a)

    def stroke_rect(self, x, y, w, h, col, lw=1.0):
        t = max(1, int(round(lw)))
        self.fill_rect(x, y, w, t, col)
        self.fill_rect(x, y + h - t, w, t, col)
        self.fill_rect(x, y, t, h, col)
        self.fill_rect(x + w - t, y, t, h, col)

    def fill_ellipse(self, x, y, w, h, col, line=None, lw=1.0):
        cx, cy, rx, ry = x + w / 2, y + h / 2, w / 2, h / 2
        for yy in range(max(0, int(y)), min(self.h, int(y + h) + 1)):
            for xx in range(max(0, int(x)), min(self.w, int(x + w) + 1)):
                d = ((xx + .5 - cx) / rx) ** 2 + ((yy + .5 - cy) / ry) ** 2
                if d <= 1.0:
                    self.blend(xx, yy, col)
                    if line and d > (1 - 2.4 * lw / max(rx, ry)):
                        self.blend(xx, yy, line)

    def png(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)
            raw += self.px[y * self.w * 3:(y + 1) * self.w * 3]

        def chunk(tag, data):
            c = struct.pack(">I", len(data)) + tag + data
            return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        out = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
               + chunk(b"IEND", b""))
        with open(path, "wb") as fh:
            fh.write(out)
        return len(out)


def render(els, path):
    c = Canvas(W, H)
    c.fill_rect(0, 0, W, H, (255, 255, 255))
    for e in els:
        if e.kind == "shape":
            x, y, w, h = e.x * S, e.y * S, e.w * S, e.h * S
            fill = rgb(e.fill) if e.fill else None
            line = rgb(e.line) if e.line else None
            if e.prst == "ellipse":
                c.fill_ellipse(x, y, w, h, fill or (255, 255, 255), line, e.lw * S)
            elif e.prst == "rightArrow":
                t = h * 0.42
                hw = min(w * .5, h * .5)
                c.fill_rect(x, y + h / 2 - t / 2, w - hw, t, fill)
                n = int(hw)
                for k in range(max(n, 1)):
                    f = k / max(n, 1)
                    c.fill_rect(x + w - hw + k, y + h / 2 - (h / 2) * (1 - f),
                                1, h * (1 - f), fill)
            elif e.prst == "downArrow":
                t = w * 0.42
                hh = min(h * .5, w * .5)
                c.fill_rect(x + w / 2 - t / 2, y, t, h - hh, fill)
                n = int(hh)
                for k in range(max(n, 1)):
                    f = k / max(n, 1)
                    c.fill_rect(x + w / 2 - (w / 2) * (1 - f), y + h - hh + k,
                                w * (1 - f), 1, fill)
            else:
                if fill:
                    c.fill_rect(x, y, w, h, fill)
                if line:
                    c.stroke_rect(x, y, w, h, line, max(1, e.lw * S))
        else:
            col = rgb(e.color)
            bold = e.font in ("HB", "TB")
            for i, ln in enumerate(e.lines):
                s = ln.upper() if e.cap else ln
                if not s.strip():
                    continue
                tw = text_w(s, e.font, e.size) * S
                tx = e.x * S
                if e.align == "c":
                    tx = (e.x + (e.w - tw / S) / 2) * S
                elif e.align == "r":
                    tx = (e.x + e.w - tw / S) * S
                ty = (e.y + e.size * (0.80 + e.lead * i)) * S
                bar = max(1.0, e.size * S * (0.46 if bold else 0.40))
                # greek each word separately so word rhythm is visible
                cx = tx
                for word in s.split(" "):
                    ww = text_w(word, e.font, e.size) * S
                    if ww > 0:
                        c.fill_rect(cx, ty - bar, ww, bar, col,
                                    0.92 if bold else 0.72)
                    cx += ww + text_w(" ", e.font, e.size) * S
    return c.png(path)


def main():
    slides = [bd.slide1(), bd.slide2(), bd.slide3(), bd.slide4(), bd.slide5(),
              bd.slide6()]
    os.makedirs(os.path.join(bd.OUT, "preview"), exist_ok=True)
    for i, s in enumerate(slides, start=1):
        p = os.path.join(bd.OUT, "preview", "slide%d.png" % i)
        n = render(s, p)
        print("slide %d -> %s (%d bytes)" % (i, p, n))


if __name__ == "__main__":
    main()
