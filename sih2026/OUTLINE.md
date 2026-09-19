# Slide-by-slide content outline

Deck: `NiyamDrishti_SIH2026_Idea.pptx` / `.pdf` — 6 slides, 13.333 × 7.5 in (960 × 540 pt).

## Template audit this deck complies with

From the official SIH 2026 idea-submission template supplied, and corroborated by
current public SIH guidance (see `SOURCES.md`):

| Rule | How this deck complies |
|---|---|
| Maximum **6** slides including the title slide | Exactly 6. The template's own "Important Instructions" slide is deleted, as it instructs |
| Section headings must not be changed | `TITLE PAGE`, `IDEA TITLE`, `TECHNICAL APPROACH`, `FEASIBILITY AND VIABILITY`, `IMPACT AND BENEFITS`, `RESEARCH AND REFERENCES` kept verbatim; slide 2 keeps the pointer heading "❖ Proposed Solution (Describe your Idea/Solution/Prototype)" |
| Idea-detail pointers must be kept | Slide 2 covers all three (detailed explanation / how it addresses the problem / innovation and uniqueness) as labelled blocks; slide 3, 4, 5 and 6 cover their pointers as panel titles |
| Points, diagrams, infographics — not paragraphs | No paragraph exceeds three lines; six diagrams, no prose blocks |
| Title-slide metadata fields | All six present in the template's order |
| Chrome | Team-name oval top-left (slides 2–6), "SMART INDIA HACKATHON 2026" wordmark top-right, blue footer bar with `@SIH Idea submission- Template` and the slide number |
| Submit as PDF | `NiyamDrishti_SIH2026_Idea.pdf` is the upload artefact |

**Two fields you must fill before upload:** `Theme` and `Team ID` / `Team Name` on slide 1
are shown as ‹placeholders›. The Problem Statement ID is written `SIH26034`, following the
2025 portal format (`SIH25108`) — confirm it against the portal.

**Logo note:** the top-right mark is a *text* wordmark, not the official artwork. If you
want the exact official logo, paste the PNG from the template file over it — every object
in the PPTX is editable and nothing is flattened.

---

## Slide 1 — TITLE PAGE
*Question answered: what problem, whose problem, and what is this?*

- `SMART INDIA HACKATHON 2026` / `TITLE PAGE` headers.
- Six metadata rows: PS ID `SIH26034`; the full official PS title; Theme ‹fill›;
  PS Category `Software`; Team ID ‹fill›; Team Name ‹fill›.
- One positioning line: *capture → extract → check → measure only when the evidence
  supports it → abstain on the record when it does not.*
- **Diagram (right):** a package face with the net-quantity declaration, a bracket marking
  "letter height", and the two possible system states — `MEASURED` (estimate with an
  uncertainty interval) and `ABSTAINED` (reason recorded, no violation inferred) — closing
  with *AI and computer vision assist observation; the officer records the legal
  determination.*

## Slide 2 — IDEA TITLE
*Question answered: what is the solution, and what is actually new about it?*

- Idea strip: NiyamDrishti — offline-first Legal Metrology screening assistant.
- **❖ Proposed Solution**, three labelled blocks:
  - *Detailed explanation* — on-device capture, extraction, versioned rule evaluation;
    the calibrated measurement path via a printed co-planar reference frame; output is a
    candidate finding with evidence, not a verdict.
  - *How it addresses the problem* — finding→crop→observation→rule version→engine version
    linkage; `PHYSICAL_SIZE_NOT_ESTABLISHED` instead of a confident violation;
    cross-face contradictions preserved; no connectivity needed.
  - *Innovation and uniqueness* — evidence-bounded measurement (interval + guard band);
    fail-closed gates before any number is shown; pre-registered, hash-checked coverage.
- **Diagram 1 (right):** the eight-step officer workflow as two vertical tracks —
  CAPTURE→IDENTIFY→EXTRACT→CHECK and MEASURE→EVIDENCE→REVIEW→REPORT, with MEASURE and
  EVIDENCE emphasised.
- **Band:** “Don’t guess.” — an unreadable condition must never become a confident
  violation.
- **Diagram 2:** where the boundary sits — AI/CV assists · system states MEASURED or
  ABSTAINED · officer decides.

## Slide 3 — TECHNICAL APPROACH
*Question answered: how does it work, and what is actually proven?*

- **Technologies to be used:** client, vision, measurement, rules, uncertainty, evidence,
  reference build — seven labelled rows, plus an explicit build-status line: *built and
  tested today is the measurement engine, its benchmark and the validation tooling; the
  Android client is the implementation target of this proposal, not a finished product.*
- **Hero diagram (right):** Known physical reference → Controlled capture → Geometry
  correction → Printed boundary estimation → Physical size estimate → Uncertainty →
  **MEASURE / ABSTAIN** → **OFFICER REVIEW**, annotated with the gate list and with the
  measurand stated as a screening proxy.
- **Validation strip (full width), three cards:**
  - green — controlled synthetic benchmark: 76 runs, 10/10 criteria PASS, max arithmetic
    error 0.008 mm, median burst SD 0.0025 mm;
  - green — abstention behaviour: 11/11 targeted unsafe cases abstained, 0 false-clear of
    4 undersized, 0 false-accuse of 4 compliant, measure rate 1.00 on safe conditions;
  - amber — physical laboratory validation: P1–P7 pre-registered and frozen, reference
    procedure and coverage committed, **laboratory validation pending, no physical claim
    made**.

## Slide 4 — FEASIBILITY AND VIABILITY
*Question answered: can this team actually do it, and what could go wrong?*

- **❖ Feasibility:** technical (reproducible pipeline, 352 tests, no third-party numerical
  stack, ~1.3 s per 12 MP frame), operational (phone + printed frame, offline, short
  protocol card), legal and ethical (screening assistance, rule-version aware,
  local-first).
- **Pre-committed stop conditions:** C1 fails → fix the maths; P1 fails → no accuracy
  claim of any kind; P2 or P6 fails → downgrade the claim; P5 fails → change the protocol,
  never the threshold. *Written down before the experiment, so a disappointing result
  cannot be answered by moving a threshold.*
- **❖ Challenges, risks and how each is handled:** six rows — curved/flexible packs
  (out of scope, 0.185 mm measured error with every gate green); no trustworthy ground
  truth (pre-registered reference procedure, P1 gates everything); uncalibrated interval
  (k = 1.645 nominal, P7 reports coverage); OCR error (source crops + contradictions
  surfaced); equipment access (documented minimum setup with machine-checked gates);
  which glyphs the rule counts (configurable threshold, measurand documented as a proxy).

## Slide 5 — IMPACT AND BENEFITS
*Question answered: who is better off, and how would we know?*

- **❖ Potential impact on the target audience** — the field officer: structured face
  coverage, evidence captured once, unreadable conditions recorded as such, reproducible
  records, supervisory re-tracing, offline operation.
- **Deliberate limits, stated up front** — scope (planar printed faces), role (screening,
  not adjudication), decision (the officer determines compliance).
- **Diagram: what “evidence-linked” means** — candidate finding → source crop → raw +
  normalised value → rule version → engine version.
- **❖ Benefits** in four groups: consumer protection, administrative, economic
  (qualitative), environmental — closing with *what will be measured as the pilot runs*
  (face coverage, abstention rate by reason code, share of findings with a complete
  evidence chain) and *no time-saving, accuracy or cost figure is claimed*.

## Slide 6 — RESEARCH AND REFERENCES
*Question answered: what is this built on, and what is still open?*

- Six external references with links (see `SOURCES.md`).
- **The open question we do not paper over:** which glyphs and faces the rule counts, and
  whether ink extent is the right reading of letter height — documented as a screening
  proxy with a configurable threshold, to be confirmed with the administering authority.
- **Our own engineering evidence:** frozen protocol and criteria; the independent
  reference method; pre-registered coverage (400 glyph instances, 20 panels, hash-checked);
  readiness audits; the reference implementation (76-run benchmark, 352 tests).
- **Repository:** `github.com/dinamsingh/Setu`, branch `niyamdrishti-phase0`, with the
  note that every synthetic figure is reproducible and that physical validation has not
  been performed.

---

## Diagram inventory (all editable vector shapes, no images)

| # | Slide | Diagram | Read time |
|---|---|---|---|
| 1 | 1 | Package face with letter-height bracket + MEASURED / ABSTAINED states | ~3 s |
| 2 | 2 | Eight-step officer workflow, two tracks | ~4 s |
| 3 | 2 | Responsibility boundary (AI assists / system states / officer decides) | ~3 s |
| 4 | 3 | Hero measurement pipeline ending in MEASURE / ABSTAIN → officer | ~5 s |
| 5 | 3 | Three-card validation status, colour-coded evidence vs pending | ~4 s |
| 6 | 5 | Evidence chain, five links | ~3 s |
