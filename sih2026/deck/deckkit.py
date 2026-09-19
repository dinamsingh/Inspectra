#!/usr/bin/env python3
"""Minimal dependency-free deck engine: one layout model -> PPTX (OOXML) + PDF.

Why hand-rolled: the sandbox has no python-pptx, no LibreOffice and no network, so
both outputs are produced from the same geometry. Text is wrapped ONCE here with real
Adobe base-14 metrics and each wrapped line is emitted as its own paragraph in the
PPTX, so PowerPoint cannot re-wrap differently from the PDF preview.

Units: points, origin top-left. 1 pt = 12700 EMU. Page 960 x 540 pt (13.333 x 7.5 in).
"""
from __future__ import annotations

import os
import zipfile
from xml.sax.saxutils import escape

PT = 12700                     # EMU per point
PAGE_W, PAGE_H = 960.0, 540.0

# --- Adobe base-14 widths (per 1000 em) -------------------------------------
_HELV = (
    "278 278 355 556 556 889 667 191 333 333 389 584 278 333 278 278 556 556 556 "
    "556 556 556 556 556 556 556 278 278 584 584 584 556 1015 667 667 722 722 667 "
    "611 778 722 278 500 667 556 833 722 778 667 778 722 667 611 722 667 944 667 "
    "667 611 278 278 278 469 556 333 556 556 500 556 556 278 556 556 222 222 500 "
    "222 833 556 556 556 556 333 500 278 556 500 722 500 500 500 334 260 334 584")
_HELVB = (
    "278 333 474 556 556 889 722 238 333 333 389 584 278 333 278 278 556 556 556 "
    "556 556 556 556 556 556 556 333 333 584 584 584 611 975 722 722 722 722 667 "
    "611 778 722 278 556 722 611 833 722 778 667 778 722 667 611 722 667 944 667 "
    "667 611 333 278 333 584 556 333 556 611 556 611 556 333 611 611 278 278 556 "
    "278 889 611 611 611 611 389 556 333 611 556 778 556 556 500 389 280 389 584")
_TIMESB = (
    "250 333 555 500 500 1000 833 278 333 333 500 570 250 333 250 278 500 500 500 "
    "500 500 500 500 500 500 500 333 333 570 570 570 500 930 722 667 722 722 667 "
    "611 778 778 389 500 778 667 944 722 778 611 778 722 556 667 722 722 1000 722 "
    "722 667 333 278 333 581 500 333 500 556 444 556 444 333 500 556 278 333 556 "
    "278 833 556 500 556 556 444 389 333 556 500 722 500 500 444 394 220 394 520")

FONTS = {
    "H": ("Arial", "Helvetica", [int(v) for v in _HELV.split()]),
    "HB": ("Arial", "Helvetica-Bold", [int(v) for v in _HELVB.split()]),
    "TB": ("Times New Roman", "Times-Bold", [int(v) for v in _TIMESB.split()]),
}


def text_w(s, font, size):
    _pptx, _pdf, w = FONTS[font]
    total = 0
    for ch in s:
        o = ord(ch)
        total += w[o - 32] if 32 <= o <= 126 else 556
    return total * size / 1000.0


def wrap(s, font, size, width):
    """Greedy wrap. Returns list of lines; honours explicit '\n'."""
    out = []
    for para in s.split("\n"):
        words, line = para.split(), ""
        if not words:
            out.append("")
            continue
        for w in words:
            trial = w if not line else line + " " + w
            if text_w(trial, font, size) <= width or not line:
                line = trial
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


# ---------------------------------------------------------------------------
# elements
# ---------------------------------------------------------------------------

class El:
    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)


def rect(x, y, w, h, fill=None, line=None, lw=0.75, r=0.0, name="rect"):
    return El("shape", prst=("roundRect" if r else "rect"), x=x, y=y, w=w, h=h,
              fill=fill, line=line, lw=lw, adj=r, name=name)


def ellipse(x, y, w, h, fill=None, line=None, lw=0.75, name="ellipse"):
    return El("shape", prst="ellipse", x=x, y=y, w=w, h=h, fill=fill, line=line,
              lw=lw, adj=0, name=name)


def arrow(x, y, w, h, fill="8AA9C6", d="right", name="arrow"):
    return El("shape", prst=("rightArrow" if d == "right" else "downArrow"),
              x=x, y=y, w=w, h=h, fill=fill, line=None, lw=0, adj=0, name=name)


def text(x, y, w, s, font="H", size=11, color="333333", align="l", lead=1.25,
         bullet=None, name="text", cap=None):
    lines = wrap(s, font, size, w - (10 if bullet else 0))
    return El("text", x=x, y=y, w=w, lines=lines, font=font, size=size,
              color=color, align=align, lead=lead, bullet=bullet, name=name,
              h=len(lines) * size * lead, cap=cap)


def bullets(x, y, w, items, font="H", size=10.5, color="333333", lead=1.22,
            gap=3.0, mark="\u2022", markcolor=None):
    """Returns (elements, height). Hanging indent, one paragraph per wrapped line."""
    els, cy = [], y
    ind = size * 0.95
    for it in items:
        ln = wrap(it, font, size, w - ind)
        els.append(El("text", x=x, y=cy, w=ind, lines=[mark], font=font, size=size,
                      color=markcolor or color, align="l", lead=lead, bullet=None,
                      name="mark", h=size * lead, cap=None))
        els.append(El("text", x=x + ind, y=cy, w=w - ind, lines=ln, font=font,
                      size=size, color=color, align="l", lead=lead, bullet=None,
                      name="bul", h=len(ln) * size * lead, cap=None))
        cy += len(ln) * size * lead + gap
    return els, cy - y - gap


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def _rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _pdf_esc(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _round_path(x, y, w, h, r):
    k = 0.5523 * r
    p = []
    p.append("%.2f %.2f m" % (x + r, y))
    p.append("%.2f %.2f l" % (x + w - r, y))
    p.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (x + w - r + k, y, x + w, y + r - k,
                                                  x + w, y + r))
    p.append("%.2f %.2f l" % (x + w, y + h - r))
    p.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (x + w, y + h - r + k,
                                                  x + w - r + k, y + h,
                                                  x + w - r, y + h))
    p.append("%.2f %.2f l" % (x + r, y + h))
    p.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (x + r - k, y + h, x, y + h - r + k,
                                                  x, y + h - r))
    p.append("%.2f %.2f l" % (x, y + r))
    p.append("%.2f %.2f %.2f %.2f %.2f %.2f c" % (x, y + r - k, x + r - k, y,
                                                  x + r, y))
    p.append("h")
    return " ".join(p)


def _arrow_path(e):
    """Flat-sided block arrow, matching the OOXML rightArrow/downArrow look."""
    x, y, w, h = e.x, PAGE_H - e.y - e.h, e.w, e.h
    if e.prst == "rightArrow":
        t = h * 0.42
        hw = min(w * 0.5, h * 0.5)
        cy = y + h / 2
        return ("%.2f %.2f m %.2f %.2f l %.2f %.2f l %.2f %.2f l %.2f %.2f l "
                "%.2f %.2f l %.2f %.2f l h" % (
                    x, cy - t / 2, x + w - hw, cy - t / 2, x + w - hw, y,
                    x + w, cy, x + w - hw, y + h, x + w - hw, cy + t / 2,
                    x, cy + t / 2))
    t = w * 0.42
    hh = min(h * 0.5, w * 0.5)
    cx = x + w / 2
    return ("%.2f %.2f m %.2f %.2f l %.2f %.2f l %.2f %.2f l %.2f %.2f l "
            "%.2f %.2f l %.2f %.2f l h" % (
                cx - t / 2, y + h, cx - t / 2, y + hh, x, y + hh,
                cx, y, x + w, y + hh, cx + t / 2, y + hh,
                cx + t / 2, y + h))


def write_pdf(path, slides):
    objs, pages = [], []

    def add(body):
        objs.append(body)
        return len(objs)          # 1-based

    font_ids = {}
    for key in ("H", "HB", "TB"):
        pdfname = FONTS[key][1]
        font_ids[key] = add("<< /Type /Font /Subtype /Type1 /BaseFont /%s "
                            "/Encoding /WinAnsiEncoding >>" % pdfname)

    for sl in slides:
        ops = []
        for e in sl:
            if e.kind == "shape":
                yy = PAGE_H - e.y - e.h
                if e.prst in ("rightArrow", "downArrow"):
                    ops.append("q %.3f %.3f %.3f rg %s f Q"
                               % (_rgb(e.fill) + (_arrow_path(e),)))
                    continue
                if e.prst == "ellipse":
                    k = 0.5523
                    cx, cy, rx, ry = e.x + e.w / 2, yy + e.h / 2, e.w / 2, e.h / 2
                    seg = ("%.2f %.2f m "
                           "%.2f %.2f %.2f %.2f %.2f %.2f c "
                           "%.2f %.2f %.2f %.2f %.2f %.2f c "
                           "%.2f %.2f %.2f %.2f %.2f %.2f c "
                           "%.2f %.2f %.2f %.2f %.2f %.2f c h" % (
                               cx + rx, cy,
                               cx + rx, cy + ry * k, cx + rx * k, cy + ry, cx, cy + ry,
                               cx - rx * k, cy + ry, cx - rx, cy + ry * k, cx - rx, cy,
                               cx - rx, cy - ry * k, cx - rx * k, cy - ry, cx, cy - ry,
                               cx + rx * k, cy - ry, cx + rx, cy - ry * k, cx + rx, cy))
                elif e.adj:
                    seg = _round_path(e.x, yy, e.w, e.h, e.adj)
                else:
                    seg = "%.2f %.2f %.2f %.2f re" % (e.x, yy, e.w, e.h)
                ops.append("q")
                if e.fill:
                    ops.append("%.3f %.3f %.3f rg" % _rgb(e.fill))
                if e.line:
                    ops.append("%.3f %.3f %.3f RG %.2f w" % (_rgb(e.line) + (e.lw,)))
                ops.append(seg + (" B" if (e.fill and e.line)
                                  else (" f" if e.fill else " S")))
                ops.append("Q")
            else:
                ops.append("q BT /F%d %.2f Tf %.3f %.3f %.3f rg"
                           % ((font_ids[e.font], e.size) + _rgb(e.color)))
                for i, ln in enumerate(e.lines):
                    s = ln.upper() if e.cap else ln
                    if not s:
                        continue
                    tw = text_w(s, e.font, e.size)
                    tx = e.x
                    if e.align == "c":
                        tx = e.x + (e.w - tw) / 2
                    elif e.align == "r":
                        tx = e.x + e.w - tw
                    ty = PAGE_H - (e.y + e.size * (0.80 + e.lead * i))
                    ops.append("1 0 0 1 %.2f %.2f Tm (%s) Tj"
                               % (tx, ty, _pdf_esc(s)))
                ops.append("ET Q")
        stream = "\n".join(ops).encode("latin-1", "replace")
        cid = add(("<< /Length %d >>\nstream\n" % len(stream))
                  + stream.decode("latin-1") + "\nendstream")
        pages.append(cid)

    kids, page_ids = [], []
    pages_id = len(objs) + len(pages) + 1
    for cid in pages:
        res = ("<< /Font << " + " ".join("/F%d %d 0 R" % (i, i)
                                         for i in font_ids.values()) + " >> >>")
        pid = add("<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] "
                  "/Resources %s /Contents %d 0 R >>"
                  % (pages_id, PAGE_W, PAGE_H, res, cid))
        page_ids.append(pid)
    kids = " ".join("%d 0 R" % p for p in page_ids)
    real_pages = add("<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(page_ids)))
    cat = add("<< /Type /Catalog /Pages %d 0 R >>" % real_pages)

    # patch parent references now that the Pages id is known
    for i, pid in enumerate(page_ids):
        objs[pid - 1] = objs[pid - 1].replace("/Parent %d 0 R" % pages_id,
                                             "/Parent %d 0 R" % real_pages)

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += ("%d 0 obj\n%s\nendobj\n" % (i, body)).encode("latin-1", "replace")
    xref = len(out)
    out += ("xref\n0 %d\n" % (len(objs) + 1)).encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode()
    out += ("trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objs) + 1, cat, xref)).encode()
    with open(path, "wb") as fh:
        fh.write(bytes(out))
    return len(page_ids)


# ---------------------------------------------------------------------------
# PPTX
# ---------------------------------------------------------------------------

_THEME = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="ND">
<a:themeElements><a:clrScheme name="ND"><a:dk1><a:srgbClr val="000000"/></a:dk1>
<a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F4E79"/></a:dk2>
<a:lt2><a:srgbClr val="EEF3F8"/></a:lt2><a:accent1><a:srgbClr val="2E75B6"/></a:accent1>
<a:accent2><a:srgbClr val="1F4E79"/></a:accent2><a:accent3><a:srgbClr val="C55A11"/></a:accent3>
<a:accent4><a:srgbClr val="2E7D32"/></a:accent4><a:accent5><a:srgbClr val="8AA9C6"/></a:accent5>
<a:accent6><a:srgbClr val="7F7F7F"/></a:accent6><a:hlink><a:srgbClr val="1F4E79"/></a:hlink>
<a:folHlink><a:srgbClr val="7F7F7F"/></a:folHlink></a:clrScheme>
<a:fontScheme name="ND"><a:majorFont><a:latin typeface="Times New Roman"/><a:ea typeface=""/>
<a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Arial"/><a:ea typeface=""/>
<a:cs typeface=""/></a:minorFont></a:fontScheme>
<a:fmtScheme name="ND"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
<a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
<a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
<a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>
<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
</a:fmtScheme></a:themeElements></a:theme>"""

_MASTER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr/></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2"
 accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5"
 accent6="accent6" hlink="hlink" folHlink="folHlink"/>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst></p:sldMaster>"""

_LAYOUT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank"
 preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>
<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld></p:sldLayout>"""


def _sp(e, sid):
    xml = ['<p:sp><p:nvSpPr><p:cNvPr id="%d" name="%s %d"/><p:cNvSpPr/><p:nvPr/>'
           '</p:nvSpPr><p:spPr><a:xfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/>'
           '</a:xfrm><a:prstGeom prst="%s"><a:avLst/></a:prstGeom>'
           % (sid, e.name, sid, round(e.x * PT), round(e.y * PT),
              round(e.w * PT), round(e.h * PT), e.prst)]
    xml.append('<a:solidFill><a:srgbClr val="%s"/></a:solidFill>' % e.fill
               if e.fill else '<a:noFill/>')
    if e.line:
        xml.append('<a:ln w="%d"><a:solidFill><a:srgbClr val="%s"/></a:solidFill>'
                   '</a:ln>' % (round(e.lw * PT), e.line))
    else:
        xml.append('<a:ln><a:noFill/></a:ln>')
    xml.append('</p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>')
    return "".join(xml)


def _tx(e, sid):
    algn = {"l": "l", "c": "ctr", "r": "r"}[e.align]
    paras = []
    for ln in e.lines:
        s = ln.upper() if e.cap else ln
        run = ('<a:r><a:rPr lang="en-IN" sz="%d" b="%d" dirty="0">'
               '<a:solidFill><a:srgbClr val="%s"/></a:solidFill>'
               '<a:latin typeface="%s"/><a:cs typeface="%s"/></a:rPr>'
               '<a:t>%s</a:t></a:r>'
               % (round(e.size * 100), 1 if e.font in ("HB", "TB") else 0,
                  e.color, FONTS[e.font][0], FONTS[e.font][0], escape(s))
               ) if s else '<a:endParaRPr lang="en-IN" sz="%d"/>' % round(e.size * 100)
        paras.append('<a:p><a:pPr algn="%s"><a:lnSpc><a:spcPct val="%d"/></a:lnSpc>'
                     '</a:pPr>%s</a:p>' % (algn, round(e.lead * 100000), run))
    return ('<p:sp><p:nvSpPr><p:cNvPr id="%d" name="%s %d"/>'
            '<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>'
            '<a:xfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            '<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0"'
            ' anchor="t"><a:noAutofit/></a:bodyPr><a:lstStyle/>%s</p:txBody></p:sp>'
            % (sid, e.name, sid, round(e.x * PT), round(e.y * PT),
               round((e.w + 3) * PT), round((e.h + e.size * 0.6) * PT),
               "".join(paras)))


def write_pptx(path, slides, title="Deck"):
    def slide_xml(els):
        body = []
        sid = 2
        for e in els:
            body.append(_sp(e, sid) if e.kind == "shape" else _tx(e, sid))
            sid += 1
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
                ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/'
                'relationships" xmlns:p="http://schemas.openxmlformats.org/'
                'presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr>'
                '<p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                '<p:grpSpPr/>%s</p:spTree></p:cSld>'
                '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
                % "".join(body))

    n = len(slides)
    ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
          'content-types"><Default Extension="rels" ContentType="application/'
          'vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/ppt/presentation.xml" ContentType="application/'
          'vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
          '<Override PartName="/ppt/slideMasters/slideMaster1.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.'
          'presentationml.slideMaster+xml"/>'
          '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.'
          'presentationml.slideLayout+xml"/>'
          '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/'
          'vnd.openxmlformats-officedocument.theme+xml"/>'
          '<Override PartName="/docProps/core.xml" ContentType="application/'
          'vnd.openxmlformats-package.core-properties+xml"/>'
          '<Override PartName="/docProps/app.xml" ContentType="application/'
          'vnd.openxmlformats-officedocument.extended-properties+xml"/>']
    for i in range(1, n + 1):
        ct.append('<Override PartName="/ppt/slides/slide%d.xml" '
                  'ContentType="application/vnd.openxmlformats-officedocument.'
                  'presentationml.slide+xml"/>' % i)
    ct.append('</Types>')

    sldids = "".join('<p:sldId id="%d" r:id="rId%d"/>' % (255 + i, i + 1)
                     for i in range(1, n + 1))
    pres = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/'
            '2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/'
            '2006/relationships" xmlns:p="http://schemas.openxmlformats.org/'
            'presentationml/2006/main">'
            '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/>'
            '</p:sldMasterIdLst><p:sldIdLst>%s</p:sldIdLst>'
            '<p:sldSz cx="%d" cy="%d"/><p:notesSz cx="%d" cy="%d"/>'
            '</p:presentation>'
            % (sldids, round(PAGE_W * PT), round(PAGE_H * PT),
               round(PAGE_H * PT), round(PAGE_W * PT)))

    pres_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
                 '2006/relationships"><Relationship Id="rId1" Type="http://schemas.'
                 'openxmlformats.org/officeDocument/2006/relationships/slideMaster" '
                 'Target="slideMasters/slideMaster1.xml"/>']
    for i in range(1, n + 1):
        pres_rels.append('<Relationship Id="rId%d" Type="http://schemas.'
                         'openxmlformats.org/officeDocument/2006/relationships/slide"'
                         ' Target="slides/slide%d.xml"/>' % (i + 1, i))
    pres_rels.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.'
                     'org/officeDocument/2006/relationships/theme" '
                     'Target="theme/theme1.xml"/></Relationships>' % (n + 2))

    z = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
    z.writestr("[Content_Types].xml", "".join(ct))
    z.writestr("_rels/.rels",
               '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
               'relationships"><Relationship Id="rId1" Type="http://schemas.'
               'openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
               'Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://'
               'schemas.openxmlformats.org/package/2006/relationships/metadata/'
               'core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" '
               'Type="http://schemas.openxmlformats.org/officeDocument/2006/'
               'relationships/extended-properties" Target="docProps/app.xml"/>'
               '</Relationships>')
    z.writestr("ppt/presentation.xml", pres)
    z.writestr("ppt/_rels/presentation.xml.rels", "".join(pres_rels))
    z.writestr("ppt/theme/theme1.xml", _THEME)
    z.writestr("ppt/slideMasters/slideMaster1.xml", _MASTER)
    z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels",
               '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
               'relationships"><Relationship Id="rId1" Type="http://schemas.'
               'openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
               'Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" '
               'Type="http://schemas.openxmlformats.org/officeDocument/2006/'
               'relationships/theme" Target="../theme/theme1.xml"/></Relationships>')
    z.writestr("ppt/slideLayouts/slideLayout1.xml", _LAYOUT)
    z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels",
               '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
               'relationships"><Relationship Id="rId1" Type="http://schemas.'
               'openxmlformats.org/officeDocument/2006/relationships/slideMaster" '
               'Target="../slideMasters/slideMaster1.xml"/></Relationships>')
    for i, els in enumerate(slides, start=1):
        z.writestr("ppt/slides/slide%d.xml" % i, slide_xml(els))
        z.writestr("ppt/slides/_rels/slide%d.xml.rels" % i,
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
                   '2006/relationships"><Relationship Id="rId1" Type="http://schemas.'
                   'openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
                   'Target="../slideLayouts/slideLayout1.xml"/></Relationships>')
    z.writestr("docProps/core.xml",
               '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/'
               'package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/'
               'elements/1.1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
               '<dc:title>%s</dc:title></cp:coreProperties>' % escape(title))
    z.writestr("docProps/app.xml",
               '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Properties xmlns="http://schemas.openxmlformats.org/'
               'officeDocument/2006/extended-properties"><Slides>%d</Slides>'
               '</Properties>' % n)
    z.close()
    return os.path.getsize(path)
