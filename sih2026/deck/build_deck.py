#!/usr/bin/env python3
"""Build the Inspectra SIH 2026 idea-submission deck (6 slides, official template).

Panels are sized from measured content, so there is no dead space and no overflow.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from deckkit import (PAGE_H, PAGE_W, arrow, bullets, ellipse, rect,  # noqa: E402
                     text, text_w, write_pdf, write_pptx)

OUT = "/projects/sandbox/sih2026"

NAVY, BLUE, MIDBLUE = "1F4E79", "2E75B6", "5B8DB8"
LIGHT, PANEL, RULE = "E8F0F8", "F6F9FC", "C3D4E4"
GREY, MUT, WHITE = "333333", "5A6672", "FFFFFF"
SAFF, GREEN = "B3541E", "2E7D32"

TEAM = "Inspectra"
FOOT = "@SIH Idea submission- Template"

L_X, L_W = 22.0, 466.0
R_X, R_W = 500.0, 438.0
TOP, BOT = 64.0, 505.0

PT_TITLE, PT_SUB, PT_BUL, PT_NOTE = 11.0, 10.4, 10.2, 9.2


# --- chrome -----------------------------------------------------------------

def mark(els):
    bx = PAGE_W - 172
    els += [rect(bx - 12, 16, 1.4, 42, fill=BLUE, name="chrome mark rule")]
    els += [text(bx, 16, 160, "SMART INDIA", "HB", 12.5, MIDBLUE, "l",
                 name="chrome mark1"),
            text(bx, 30, 160, "HACKATHON", "HB", 12.5, NAVY, "l",
                 name="chrome mark2"),
            text(bx, 44, 160, "2026", "HB", 12.5, NAVY, "l", name="chrome mark3")]
    return els


def chrome(title, page):
    e = [text(118, 20, 700, title, "TB", 25, NAVY, "c", name="chrome title"),
         rect(118, 54, 700, 1.4, fill=BLUE, name="chrome rule"),
         ellipse(20, 12, 84, 46, fill=WHITE, line=NAVY, lw=1.0,
                 name="chrome team badge"),
         text(20, 25, 84, TEAM, "HB", 9.5, NAVY, "c", name="chrome team"),
         rect(0, PAGE_H - 24, PAGE_W, 24, fill=BLUE, name="chrome footer"),
         text(0, PAGE_H - 17, PAGE_W, FOOT, "H", 8.5, WHITE, "c",
              name="chrome foot text"),
         text(PAGE_W - 34, PAGE_H - 17, 20, str(page), "HB", 9, WHITE, "r",
              name="chrome page")]
    return mark(e)


def panel(x, y, w, h, title=None, fill=PANEL, tcolor=NAVY, name="panel"):
    els = [rect(x, y, w, h, fill=fill, line=RULE, lw=0.9, r=4, name=name)]
    if title:
        els += [rect(x, y, w, 24, fill=LIGHT, line=None, r=4, name=name + " head"),
                rect(x, y + 23.1, w, 0.9, fill=RULE, name="hd rule"),
                text(x + 11, y + 7, w - 22, title, "HB", PT_TITLE, tcolor, "l")]
    return els


def sub(x, y, w, label, color=SAFF, size=PT_SUB):
    return [rect(x, y + 3.0, 3.2, 9.5, fill=color, name="tick"),
            text(x + 9, y + 1.2, w - 9, label, "HB", size, color, "l")], 16.0


def kv(x, y, w, lab, val, lw=96.0, ls=PT_SUB, vs=PT_BUL, lcol=NAVY, lead=1.26):
    """Label + wrapped value on one row. Returns (els, height)."""
    t = text(x + lw, y, w - lw, val, "H", vs, GREY, "l", lead=lead)
    return [text(x, y, lw - 8, lab, "HB", ls, lcol, "l"), t], max(t.h, ls * 1.3)


# --- slide 1 ----------------------------------------------------------------

def slide1():
    e = mark([text(0, 22, PAGE_W - 196, "SMART INDIA HACKATHON 2026", "TB", 31, NAVY,
                   "c", name="s1 hero"),
              text(22, 72, 556, "TITLE PAGE", "TB", 22, GREY, "c", name="s1 sub"),
              text(PAGE_W - 40, 518, 24, "1", "H", 9.5, MUT, "r", name="s1 page")])

    rows = [
        ("Problem Statement ID", "SIH26034"),
        ("Problem Statement Title",
         "Software System to check compliance of Packaged Commodities under Legal "
         "Metrology (Packaged Commodities) Rules, 2011 by scanning products, images "
         "and labels."),
        ("Theme", "\u2039Theme as listed on the SIH portal\u203a"),
        ("PS Category", "Software"),
        ("Team ID", "\u2039Team ID\u203a"),
        ("Team Name (Registered on portal)", "\u2039Team name as registered\u203a"),
    ]
    y, w = 118.0, 556.0
    for label, val in rows:
        e += [rect(22, y + 5.0, 4.5, 4.5, fill=NAVY, r=2, name="dot")]
        lw = text_w(label + "- ", "HB", 12.4)
        e += [text(36, y, lw, label + "-", "HB", 12.4, GREY, "l")]
        t = text(36 + lw, y, w - lw, val, "H", 12.4, GREY, "l", lead=1.32)
        e.append(t)
        y += max(t.h, 16) + 15.0

    e += [rect(22, 452, 556, 1.2, fill=RULE, name="s1 rule")]
    e += [text(22, 462, 556,
               "Offline-first field assistant: capture the package, extract the "
               "declarations, check them against the rules of that date, measure "
               "letter height only when the evidence supports it \u2014 and abstain, "
               "on the record, when it does not.",
               "H", 10.4, MUT, "l", lead=1.32, name="s1 tag")]

    # meaning mark: a package face with the measured declaration
    px, py = 624.0, 112.0
    e += panel(px - 20, py - 26, 318, 340, fill=WHITE, name="s1 mark panel")
    e += [rect(px, py, 214, 170, fill="FAFCFE", line=NAVY, lw=1.4, r=6,
               name="package face")]
    e += [text(px + 16, py + 15, 180, "NET QUANTITY", "HB", 9.4, MUT, "l")]
    for i, (lab, sz) in enumerate((("500 g", 17.0), ("M.R.P. Rs 145.00", 12.0),
                                   ("Mfd: 03/2026", 9.6))):
        e += [text(px + 16, py + 33 + i * 29, 180, lab, "HB", sz, GREY, "l")]
    e += [rect(px + 16, py + 126, 182, 0.8, fill=RULE, name="sep")]
    e += [text(px + 16, py + 135, 182, "Packer: name & address", "H", 8.6, MUT, "l")]
    bx = px + 192
    e += [rect(bx, py + 33, 1.0, 21, fill=SAFF, name="h bar"),
          rect(bx - 4.5, py + 33, 10, 1.0, fill=SAFF, name="h cap t"),
          rect(bx - 4.5, py + 53, 10, 1.0, fill=SAFF, name="h cap b"),
          text(bx + 11, py + 36, 92, "letter height", "HB", 8.6, SAFF, "l")]

    yy = py + 192
    for lab, val, col in (
            ("MEASURED", "millimetre estimate with an uncertainty interval", GREEN),
            ("ABSTAINED", "reason recorded; no violation inferred", SAFF)):
        e += [rect(px, yy, 96, 22, fill=("E7F0E8" if col == GREEN else "F6EAE2"),
                   line=col, lw=1.0, r=3, name="state chip")]
        e += [text(px, yy + 6, 96, lab, "HB", 9.4, col, "c")]
        t = text(px + 106, yy + 1, 172, val, "H", 8.8, GREY, "l", lead=1.22)
        e.append(t)
        yy += 30
    e += [rect(px, yy + 6, 278, 1, fill=RULE, name="s1 mr")]
    e += [text(px, yy + 16, 278,
               "AI and computer vision assist observation. The officer records the "
               "legal determination.", "H", 8.8, MUT, "l", lead=1.26)]
    return e


# --- slide 2 ----------------------------------------------------------------

def slide2():
    e = chrome("IDEA TITLE", 2)
    e += [rect(22, 60, 916, 23, fill=LIGHT, line=RULE, lw=0.8, r=3, name="idea strip")]
    e += [text(33, 66, 900, "Inspectra \u2014 offline-first Legal Metrology "
               "screening assistant for packaged commodities:  capture \u2192 extract "
               "\u2192 check \u2192 measure-or-abstain \u2192 evidence-linked report",
               "HB", 10.6, NAVY, "l")]

    y0 = 90.0
    c, y = [], y0 + 32
    for label, items in (
        ("Detailed explanation", [
            "Android app for a Legal Metrology inspection: the officer captures the "
            "package faces, the app extracts the declarations, evaluates a versioned "
            "rule pack and assembles the record \u2014 entirely on-device.",
            "Character-height declarations add a calibrated path: a printed co-planar "
            "reference frame turns a phone photo into a millimetre estimate.",
            "The output is a candidate finding with its evidence, not a verdict."]),
        ("How it addresses the problem", [
            "Every finding links to its source crop, raw and normalised observation, "
            "rule version and engine version, so a reviewer can re-trace it.",
            "Unreadable or unsuitable evidence returns PHYSICAL_SIZE_NOT_ESTABLISHED "
            "instead of a confident violation.",
            "Contradictions across faces \u2014 two different MRPs, for instance \u2014 "
            "are preserved and flagged, never silently resolved.",
            "No connectivity is needed in a shop or godown; sync is optional."]),
        ("Innovation and uniqueness of the solution", [
            "Evidence-bounded measurement: every millimetre figure carries an "
            "uncertainty interval and a guard-band decision.",
            "Fail-closed gates \u2014 calibration, geometry, image quality, "
            "segmentation, burst spread, uncertainty \u2014 run before any number is "
            "shown.",
            "Face and glyph coverage is pre-registered and hash-checked, so nothing "
            "is selected after a result is seen."])):
        s, dh = sub(L_X + 11, y, L_W - 22, label)
        c += s; y += dh
        b, h = bullets(L_X + 15, y, L_W - 30, items, size=PT_BUL)
        c += b; y += h + 12
    e += panel(L_X, y0, L_W, y - 12 - y0 + 10,
               "\u2756 Proposed Solution (Describe your Idea/Solution/Prototype)") + c

    # workflow: two vertical tracks
    steps_a = [("CAPTURE", "package faces"), ("IDENTIFY", "product & faces"),
               ("EXTRACT", "declarations (OCR)"), ("CHECK", "rule pack, by date")]
    steps_b = [("MEASURE", "or abstain"), ("EVIDENCE", "crop + hash link"),
               ("REVIEW", "officer confirms"), ("REPORT", "canonical JSON + PDF")]
    bw, bh, gap = 190.0, 28.0, 10.0
    wh = 32 + 4 * bh + 3 * gap + 12
    c = []
    for col, steps in enumerate((steps_a, steps_b)):
        bx = R_X + 14 + col * (bw + 30)
        for i, (st, nt) in enumerate(steps):
            by = y0 + 32 + i * (bh + gap)
            hot = st in ("MEASURE", "EVIDENCE")
            c += [rect(bx, by, bw, bh, fill=(LIGHT if hot else WHITE),
                       line=(NAVY if hot else RULE), lw=(1.0 if hot else 0.8), r=3,
                       name="step")]
            c += [rect(bx, by, 3.4, bh, fill=(SAFF if hot else MIDBLUE), r=2,
                       name="step tick")]
            c += [text(bx + 12, by + 5, 110, st, "HB", 9.6, NAVY, "l")]
            c += [text(bx + 12, by + 16.5, bw - 22, nt, "H", 8.2, MUT, "l")]
            if i < 3:
                c += [arrow(bx + bw / 2 - 5, by + bh + 1, 10, gap - 2, MIDBLUE,
                            d="down")]
    c += [arrow(R_X + 14 + bw + 6, y0 + 32 + 1.5 * (bh + gap), 18, 14, MIDBLUE)]
    e += panel(R_X, y0, R_W, wh, "Field officer workflow") + c

    yy = y0 + wh + 10
    e += [rect(R_X, yy, R_W, 48, fill=NAVY, r=4, name="philosophy")]
    e += [text(R_X + 16, yy + 10, 150, "\u201cDon\u2019t guess.\u201d", "TB", 17,
               WHITE, "l")]
    e += [text(R_X + 152, yy + 9, R_W - 168,
               "An unreadable or unsuitable condition must never become a confident "
               "violation. The system states what it could not establish.",
               "H", 9.4, "DCE6F0", "l", lead=1.3)]

    yy += 58
    c, ry = [], yy + 32
    for lab, val, col in (
            ("AI / CV assists", "detection, OCR, boundary estimation, gating", NAVY),
            ("System states", "MEASURED with an interval  \u00b7  or ABSTAINED with a "
                              "reason code", NAVY),
            ("Officer decides", "reviews the evidence and records the legal "
                                "determination", SAFF)):
        b, h = kv(R_X + 15, ry, R_W - 30, lab, val, lw=104, lcol=col)
        c += b; ry += h + 8
    e += panel(R_X, yy, R_W, ry - 8 - yy + 10, "Where the boundary sits") + c
    return e


# --- slide 3 ----------------------------------------------------------------

def slide3():
    e = chrome("TECHNICAL APPROACH", 3)
    y0 = 62.0
    c, y = [], y0 + 32
    for lab, val in (
        ("Client", "Android (Kotlin), offline-first; encrypted local store; optional "
                   "idempotent sync"),
        ("Vision", "on-device OCR with face and declaration-line detection; every "
                   "crop retained as evidence"),
        ("Measurement", "four-marker co-planar fiducial, homography rectification, "
                        "sub-pixel 50 % linearised-luminance ink boundary, "
                        "model-fitted extremes"),
        ("Rules", "signed, versioned rule pack selected by inspection date; "
                  "deterministic three/four-valued logic"),
        ("Uncertainty", "component budget \u2192 combined u_c; k = 1.645, reported as "
                        "nominal and not yet calibrated"),
        ("Evidence", "canonical JSON plus an offline PDF, hash-linked; role-based "
                     "review"),
        ("Reference build", "pure-Python measurement engine with no third-party "
                            "numerical stack; 352 automated tests; deterministic "
                            "re-runs"),
    ):
        b, h = kv(L_X + 12, y, L_W - 24, lab, val, lw=100)
        c += b; y += h + 8
    c += [rect(L_X + 12, y - 1, L_W - 24, 1, fill=RULE, name="tech rule")]
    c += [text(L_X + 12, y + 8, L_W - 24,
               "Built and tested today: the measurement engine, its benchmark and the "
               "validation tooling. The Android client is the implementation target of "
               "this proposal, not a finished product.",
               "H", 9.0, MUT, "l", lead=1.28, name="build status")]
    y += 8 + 2 * 9.0 * 1.28
    e += panel(L_X, y0, L_W, y - y0 + 12, "Technologies to be used") + c
    left_end = y + 12

    # hero pipeline
    stages = ["Known physical reference", "Controlled capture", "Geometry correction",
              "Printed boundary estimation", "Physical size estimate", "Uncertainty"]
    c, sy = [], y0 + 34
    for i, st in enumerate(stages):
        c += [rect(R_X + 16, sy, 248, 24, fill=WHITE, line=RULE, lw=0.8, r=3,
                   name="stage")]
        c += [text(R_X + 27, sy + 6.4, 232, st, "HB", 9.6, NAVY, "l")]
        if i < len(stages) - 1:
            c += [arrow(R_X + 135, sy + 24.5, 10, 6.5, MIDBLUE, d="down")]
        sy += 31
    sy += 4
    c += [rect(R_X + 16, sy, 116, 28, fill="E7F0E8", line=GREEN, lw=1.1, r=3,
               name="measured")]
    c += [text(R_X + 16, sy + 8.4, 116, "MEASURE", "HB", 10.4, GREEN, "c")]
    c += [rect(R_X + 148, sy, 116, 28, fill="F6EAE2", line=SAFF, lw=1.1, r=3,
               name="abstain")]
    c += [text(R_X + 148, sy + 8.4, 116, "ABSTAIN", "HB", 10.4, SAFF, "c")]
    c += [arrow(R_X + 272, sy + 7, 14, 14, MIDBLUE)]
    c += [rect(R_X + 292, sy, 132, 28, fill=NAVY, r=3, name="officer")]
    c += [text(R_X + 292, sy + 8.4, 132, "OFFICER REVIEW", "HB", 9.6, WHITE, "c")]
    c += [text(R_X + 278, y0 + 40, 146,
               "Fail-closed gates choose the branch: calibration, geometry, image "
               "quality, segmentation, burst spread, uncertainty. A gate that cannot "
               "be satisfied abstains.", "H", 8.8, MUT, "l", lead=1.32)]
    c += [text(R_X + 278, y0 + 136, 146,
               "The measurand is documented explicitly \u2014 visible printed-ink "
               "extent perpendicular to the fitted baseline \u2014 and labelled a "
               "screening proxy, not a statutory definition.",
               "H", 8.8, MUT, "l", lead=1.32)]
    right_end = sy + 28 + 12
    e += panel(R_X, y0, R_W, right_end - y0,
               "Methodology \u2014 how a photo becomes a bounded millimetre estimate")
    e += c

    # validation strip
    vy = max(left_end, right_end) + 12
    cw = (PAGE_W - 2 * L_X - 36) / 3
    cards = [
        ("Controlled synthetic benchmark", GREEN, "E7F0E8", [
            "76 runs, 10 of 10 pre-registered criteria PASS",
            "max arithmetic error 0.008 mm on ideal renders",
            "median burst repeatability SD 0.0025 mm"]),
        ("Abstention behaviour, same benchmark", GREEN, "E7F0E8", [
            "11 of 11 targeted unsafe cases abstained",
            "0 false-clear of 4 undersized; 0 false-accuse of 4 compliant",
            "measure rate 1.00 under safe conditions"]),
        ("Physical laboratory validation", SAFF, "F6EAE2", [
            "P1\u2013P7 acceptance criteria pre-registered and frozen",
            "reference procedure, glyph map and panel selection committed",
            "laboratory validation pending \u2014 no physical claim is made"]),
    ]
    c, hmax = [], 0.0
    for i, (h, col, fill, items) in enumerate(cards):
        cx = L_X + 12 + i * (cw + 6)
        tt = text(cx + 10, vy + 40, cw - 20, h, "HB", 9.8, col, "l", lead=1.2)
        b, bh = bullets(cx + 10, vy + 40 + tt.h + 6, cw - 20, items, size=8.8,
                        lead=1.22, gap=2.5, mark="\u2013", markcolor=col)
        inner = tt.h + 6 + bh + 18
        hmax = max(hmax, inner)
        c += [("card", cx, inner)] + [tt] + b
    body = [x for x in c if not isinstance(x, tuple)]
    boxes = [rect(cx, vy + 32, cw, hmax, fill=f, line=cl, lw=0.9, r=3, name="vcard")
             for (cx, (h, cl, f, it)) in
             [(L_X + 12 + i * (cw + 6), cards[i]) for i in range(3)]]
    e += panel(L_X, vy, PAGE_W - 2 * L_X, 32 + hmax + 12,
               "Validation status \u2014 what is evidence today, and what is not")
    e += boxes + body
    return e


# --- slide 4 ----------------------------------------------------------------

def slide4():
    e = chrome("FEASIBILITY AND VIABILITY", 4)
    y0 = 62.0
    c, y = [], y0 + 32
    for label, items in (
        ("Technical", [
            "The measurement pipeline is implemented and reproducible: re-runs are "
            "bit-identical and 352 automated tests pass.",
            "No third-party numerical stack, so the same arithmetic ports to the "
            "device.",
            "Measured cost about 1.3 s per 12 MP frame single-threaded \u2014 a burst "
            "takes seconds."]),
        ("Operational", [
            "The field kit is a phone plus a printed co-planar reference frame; no "
            "bench instrument travels to the shop.",
            "Offline by design: the inspection completes with no network.",
            "Training is a short protocol card, because the app refuses conditions it "
            "cannot handle."]),
        ("Legal and ethical", [
            "Screening assistance: the officer records the determination, the app "
            "records the evidence.",
            "Rule-version aware and date-selected, so a past inspection stays "
            "evaluable under the rules of its own date.",
            "Local-only storage by default; sync is opt-in."])):
        s, dh = sub(L_X + 11, y, L_W - 22, label)
        c += s; y += dh
        b, h = bullets(L_X + 15, y, L_W - 30, items, size=PT_BUL)
        c += b; y += h + 11
    e += panel(L_X, y0, L_W, y - 11 - y0 + 10, "\u2756 Feasibility of the idea") + c
    ly = y - 11 + 10 + 12

    # stop conditions (pre-committed, from the frozen criteria)
    c, sy = [], ly + 32
    for lab, val in (("C1 fails", "the pipeline arithmetic is wrong \u2014 fix before "
                                  "any physical work"),
                     ("P1 fails", "no usable ground truth \u2014 no accuracy claim of "
                                  "any kind"),
                     ("P2 or P6 fails", "the measurement claim is downgraded"),
                     ("P5 fails", "the capture protocol changes, never the threshold")):
        b, h = kv(L_X + 14, sy, L_W - 28, lab, val, lw=104, ls=9.6, vs=9.4)
        c += b; sy += h + 6.5
    c += [text(L_X + 14, sy + 2, L_W - 28,
               "Written down before the experiment, so a disappointing result cannot "
               "be answered by moving a threshold.", "H", 8.8, MUT, "l", lead=1.28)]
    e += panel(L_X, ly, L_W, sy + 2 + 22 - ly,
               "Pre-committed stop conditions") + c

    c, y = [], y0 + 32
    risks = [
        ("Curved, flexible or embossed packs",
         "Declared out of scope. Out-of-plane print is invisible to a single view "
         "\u2014 measured 0.185 mm error with every gate green \u2014 so flatness is a "
         "fixture requirement and the app abstains instead."),
        ("No trustworthy ground truth",
         "An independent reference procedure is pre-registered: a 2400 dpi scan as "
         "primary and a measuring-microscope cross-check, with criterion P1 gating "
         "every accuracy claim."),
        ("The interval is not yet calibrated",
         "k = 1.645 is reported as nominal. P7 collects empirical coverage as "
         "calibration evidence and can never be shown as a validated interval."),
        ("OCR or transcription error",
         "Every field keeps its source crop for officer review, and cross-face "
         "contradictions are surfaced rather than resolved."),
        ("Reference equipment access",
         "The minimum setup is documented \u2014 2400 dpi scanner, certified length "
         "standard, measuring microscope \u2014 with machine-checked readiness gates "
         "before capture."),
        ("Which glyphs the rule counts",
         "The threshold is configurable per rule version, and the measurand is "
         "documented as a proxy pending confirmation with the administering "
         "authority."),
    ]
    for lab, val in risks:
        c += [rect(R_X + 13, y + 3.2, 3.2, 9.5, fill=SAFF, name="rtick")]
        c += [text(R_X + 22, y + 1.2, R_W - 36, lab, "HB", 9.8, NAVY, "l")]
        t = text(R_X + 22, y + 15.4, R_W - 36, val, "H", 9.3, GREY, "l", lead=1.28)
        c.append(t)
        y += 15.6 + t.h + 8.5
    e += panel(R_X, y0, R_W, y - 8.5 - y0 + 10,
               "\u2756 Challenges, risks and how each is handled") + c
    return e


# --- slide 5 ----------------------------------------------------------------

def slide5():
    e = chrome("IMPACT AND BENEFITS", 5)
    y0 = 62.0
    c = [text(L_X + 12, y0 + 32, L_W - 24,
              "Primary user: the Legal Metrology field officer or inspector.",
              "HB", PT_SUB, SAFF, "l")]
    b, h = bullets(L_X + 15, y0 + 52, L_W - 30, [
        "A structured pass over the package faces, with coverage tracked instead of "
        "remembered.",
        "Evidence captured once at the point of inspection, so declarations are not "
        "re-typed later.",
        "Conditions that cannot be read are recorded as such: the officer is told "
        "what was not established.",
        "A reproducible record \u2014 same inputs, same output \u2014 with rule and "
        "engine versions attached.",
        "Supervisory review becomes re-tracing evidence instead of reconstructing a "
        "visit.",
        "Works in a shop, godown or checkpoint with no connectivity.",
    ], size=PT_BUL)
    c += b
    e += panel(L_X, y0, L_W, 52 + h + 12,
               "\u2756 Potential impact on the target audience") + c
    ly = y0 + 52 + h + 12 + 12

    c = []
    lims = [("Scope", "planar printed faces, controlled capture"),
            ("Role", "screening assistance, not adjudication"),
            ("Decision", "the officer determines compliance")]
    lx = L_X + 13
    cw = (L_W - 26) / 3
    for lab, val in lims:
        c += [text(lx, ly + 32, cw - 10, lab, "HB", 9.8, NAVY, "l")]
        c += [text(lx, ly + 46, cw - 10, val, "H", 9.0, MUT, "l", lead=1.24)]
        lx += cw
    c += [text(L_X + 13, ly + 82, L_W - 26,
               "Stating this on the record is part of the design: a screening tool "
               "that overstates its reach is worse than one that refuses a case.",
               "H", 9.0, GREY, "l", lead=1.3)]
    e += panel(L_X, ly, L_W, 112, "Deliberate limits, stated up front") + c
    ey = ly + 112 + 12

    # evidence chain: what "evidence-linked" actually means
    chain = ["Candidate finding", "Source crop", "Raw + normalised value",
             "Rule version", "Engine version"]
    c, cx = [], L_X + 13
    bwid = (L_W - 26 - 4 * 11) / 5
    for i, st in enumerate(chain):
        c += [rect(cx, ey + 32, bwid, 30, fill=WHITE, line=RULE, lw=0.8, r=3,
                   name="chain")]
        c += [rect(cx, ey + 32, bwid, 2.6, fill=MIDBLUE, name="chain tick")]
        lines = text(cx + 5, ey + 39, bwid - 10, st, "HB", 8.2, NAVY, "c", lead=1.16)
        c.append(lines)
        if i < 4:
            c += [arrow(cx + bwid + 1.5, ey + 43, 8, 8, MIDBLUE)]
        cx += bwid + 11
    c += [text(L_X + 13, ey + 70, L_W - 26,
               "Each link is stored, so a supervisor can re-trace a finding to the "
               "pixel it came from and to the rule text that was in force.",
               "H", 8.8, MUT, "l", lead=1.26)]
    e += panel(L_X, ey, L_W, 118, "What \u201cevidence-linked\u201d means here") + c

    c, y = [], y0 + 32
    for label, items in (
        ("Consumer protection (social)", [
            "Declarations are screened consistently rather than from recall of the "
            "rule text.",
            "Weak evidence produces an abstention, so a compliant packer is less "
            "likely to be wrongly accused."]),
        ("Administrative", [
            "Uniform, machine-readable records with a lineage that runs from the "
            "finding back to the pixel.",
            "Coverage and abstention rates become visible quantities a supervisor "
            "can act on."]),
        ("Economic (qualitative)", [
            "Commodity hardware and an offline workflow, so no per-site "
            "infrastructure is needed.",
            "Open, versioned rule packs keep maintenance inside the department."]),
        ("Environmental", [
            "A paperless inspection record produced on the device, printed only when "
            "a case requires it."])):
        s, dh = sub(R_X + 11, y, R_W - 22, label, color=NAVY)
        c += s; y += dh
        b, h = bullets(R_X + 15, y, R_W - 30, items, size=PT_BUL, lead=1.24)
        c += b; y += h + 13
    y += 4
    c += [rect(R_X + 13, y, R_W - 26, 1, fill=RULE, name="brule")]
    c += [text(R_X + 13, y + 10, R_W - 26,
               "Measured as the pilot runs, not asserted here: face coverage per "
               "inspection, abstention rate by reason code, and the share of findings "
               "with a complete evidence chain.", "H", 9.0, GREY, "l", lead=1.3)]
    c += [text(R_X + 13, y + 50, R_W - 26,
               "No time-saving, accuracy or cost figure is claimed: none has been "
               "measured in the field yet.", "H", 8.8, MUT, "l", lead=1.3)]
    e += panel(R_X, y0, R_W, y + 78 - y0, "\u2756 Benefits of the solution") + c
    return e


# --- slide 6 ----------------------------------------------------------------

def slide6():
    e = chrome("RESEARCH  AND REFERENCES", 6)
    y0 = 62.0
    c, y = [], y0 + 32
    refs = [
        ("Legal Metrology (Packaged Commodities) Rules, 2011",
         "Mandatory declarations on pre-packaged commodities, and their size and "
         "legibility. Department of Consumer Affairs.",
         "consumeraffairs.nic.in"),
        ("Legal Metrology Act, 2009",
         "Enabling statute for the Rules and for enforcement powers.",
         "consumeraffairs.nic.in"),
        ("Consolidated Rules text used to build the rule model",
         "The 2011 Rules with amendments, as hosted for public reference.",
         "bombayhighcourt.gov.in/bhc/libweb/legislation/rulec/"
         "LegalMetrologyPackagedCommoditiesRules,2011.pdf"),
        ("OIML R 79 \u2014 Labelling requirements for prepackaged products",
         "International reference for declaration and legibility requirements.",
         "oiml.org/en/publications"),
        ("JCGM 100:2008 (GUM) \u2014 Evaluation of measurement data",
         "The method used for the component uncertainty budget and coverage factor.",
         "bipm.org"),
        ("Problem statement SIH26034",
         "Ministry of Consumer Affairs, Food & Public Distribution \u2014 Department "
         "of Consumer Affairs.",
         "sih.gov.in"),
    ]
    for i, (t1, t2, link) in enumerate(refs, start=1):
        c += [text(L_X + 12, y, 18, "%d." % i, "HB", 9.4, NAVY, "l")]
        t = text(L_X + 32, y, L_W - 48, t1, "HB", 9.4, NAVY, "l", lead=1.2)
        c.append(t); yy = y + t.h + 1.5
        t = text(L_X + 32, yy, L_W - 48, t2, "H", 8.9, GREY, "l", lead=1.24)
        c.append(t); yy += t.h + 1.5
        t = text(L_X + 32, yy, L_W - 48, link, "H", 8.5, BLUE, "l", lead=1.2)
        c.append(t)
        y = yy + t.h + 7.5
    e += panel(L_X, y0, L_W, y - 10 - y0 + 10,
               "Regulatory and metrological references") + c
    oy = y - 10 + 10 + 12

    c, sy = [], oy + 30
    for lab, val in (
            ("Open question", "which glyphs and faces the rule counts, and whether "
                              "ink extent is the right reading of letter height"),
            ("Our position", "documented as a screening proxy with a configurable "
                             "threshold per rule version, to be confirmed with the "
                             "administering authority before any compliance wording "
                             "is finalised")):
        b, h = kv(L_X + 14, sy, L_W - 28, lab, val, lw=96, ls=9.4, vs=9.0)
        c += b; sy += h + 6
    e += panel(L_X, oy, L_W, sy - 6 - oy + 11,
               "The open question we do not paper over") + c

    c, y = [], y0 + 32
    ours = [
        ("Frozen protocol and criteria",
         "P0_PROTOCOL.md and P0_CRITERIA.md \u2014 the capture protocol and the "
         "pre-registered P1\u2013P7 acceptance bands."),
        ("Independent reference method",
         "P0_REFERENCE_PROCEDURE.md \u2014 scanner-primary, microscope cross-check, "
         "and the independence rules between them."),
        ("Pre-registered coverage",
         "glyph_map.json, 400 glyph instances; glyph_selection.json, 20 panels \u2014 "
         "both derived by rule and hash-checked."),
        ("Readiness audits",
         "Reference setup, flatness control and equipment inventory, each with a "
         "machine-checked gate."),
        ("Reference implementation",
         "Pure-Python measurement engine, a 76-run synthetic benchmark with its "
         "analysis output, and 352 automated tests."),
    ]
    for lab, val in ours:
        c += [rect(R_X + 13, y + 3.2, 3.2, 9.5, fill=MIDBLUE, name="otick")]
        c += [text(R_X + 22, y + 1.2, R_W - 36, lab, "HB", 9.8, NAVY, "l")]
        t = text(R_X + 22, y + 15.2, R_W - 36, val, "H", 9.2, GREY, "l", lead=1.26)
        c.append(t)
        y += 15.4 + t.h + 7
    e += panel(R_X, y0, R_W, y - 7 - y0 + 10,
               "Our own engineering evidence (this project)") + c
    ry = y - 7 + 10 + 12

    c = [text(R_X + 13, ry + 32, R_W - 26,
              "github.com/dinamsingh/Inspectra   \u00b7   branch main",
              "HB", 9.8, BLUE, "l"),
         text(R_X + 13, ry + 50, R_W - 26,
              "Holds the measurement engine, the synthetic benchmark and its analysis "
              "output, the frozen protocol and criteria, the pre-registered coverage "
              "files, the readiness audits and the test suite. Private repository "
              "\u2014 access on request.", "H", 9.0, GREY, "l", lead=1.28),
         rect(R_X + 13, ry + 116, R_W - 26, 1, fill=RULE, name="rr"),
         text(R_X + 13, ry + 126, R_W - 26,
              "Every synthetic figure quoted in this deck is reproducible from the "
              "repository. Physical laboratory validation has not been performed and "
              "is not claimed anywhere in this deck.",
              "H", 9.0, MUT, "l", lead=1.28)]
    e += panel(R_X, ry, R_W, 172, "Repository") + c
    return e


# --- QA ---------------------------------------------------------------------

def qa(slides):
    bad = []
    for i, els in enumerate(slides, start=1):
        for e in els:
            h = getattr(e, "h", 0.0)
            if (e.x < 0 or e.y < 0 or e.x + e.w > PAGE_W + 0.5
                    or e.y + h > PAGE_H + 0.5):
                bad.append("S%d %s outside page (x=%.1f y=%.1f w=%.1f h=%.1f)"
                           % (i, e.name, e.x, e.y, e.w, h))
            if not e.name.startswith("chrome") and not e.name.startswith("s1 "):
                if e.y + h > BOT + 1.0:
                    bad.append("S%d %s below content area: y+h=%.1f > %.1f"
                               % (i, e.name, e.y + h, BOT))
            if e.kind == "text":
                for ln in e.lines:
                    tw = text_w(ln.upper() if e.cap else ln, e.font, e.size)
                    if tw > e.w + 3.5:
                        bad.append("S%d %s overflow %.1f>%.1f %r"
                                   % (i, e.name, tw, e.w, ln[:40]))
    return bad


def fill_ratio(els):
    """Share of the content area covered by any element bounding box (coarse)."""
    cells = set()
    for e in els:
        h = getattr(e, "h", 0.0)
        if e.name.startswith("chrome"):
            continue
        for gx in range(int(e.x // 16), int((e.x + e.w) // 16) + 1):
            for gy in range(int(e.y // 16), int((e.y + max(h, 2)) // 16) + 1):
                cells.add((gx, gy))
    return len(cells) / ((PAGE_W / 16) * (PAGE_H / 16))


def main():
    os.makedirs(OUT, exist_ok=True)
    slides = [slide1(), slide2(), slide3(), slide4(), slide5(), slide6()]
    bad = qa(slides)
    print("QA: %d issue(s)" % len(bad))
    for p in bad:
        print("  " + p)
    pptx = os.path.join(OUT, "Inspectra_SIH2026_Idea.pptx")
    pdf = os.path.join(OUT, "Inspectra_SIH2026_Idea.pdf")
    size = write_pptx(pptx, slides, "Inspectra - SIH 2026 (PS SIH26034)")
    pages = write_pdf(pdf, slides)
    print("pptx %d bytes, %d slides, %d shapes | pdf %d pages"
          % (size, len(slides), sum(len(s) for s in slides), pages))
    for i, s in enumerate(slides, start=1):
        low = max(e.y + getattr(e, "h", 0.0) for e in s
                  if not e.name.startswith("chrome"))
        print("  slide %d: %3d objects, content bottom %.1f, fill %.0f%%"
              % (i, len(s), low, 100 * fill_ratio(s)))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
