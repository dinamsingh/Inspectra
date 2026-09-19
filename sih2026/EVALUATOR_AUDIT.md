# Adversarial evaluator review, and what was changed because of it

Read as an SIH screening evaluator seeing the deck cold, with no narration.

## 1. What would make me doubt the solution?

| Doubt | Verdict | Action taken |
|---|---|---|
| "They are measuring millimetres from a phone photo — that cannot work." | Fair suspicion. | The hero pipeline on slide 3 shows *why* it can be bounded: a known physical reference, then geometry correction, then a boundary estimate, then an uncertainty figure, then a **branch** that can refuse. The word "abstain" appears on four slides. A reviewer sees the humility before the claim. |
| "Are those accuracy numbers real, or lab results dressed up?" | The single biggest risk in a deck like this. | Every figure sits inside a card **titled** *Controlled synthetic benchmark*, in green, beside an amber card titled *Physical laboratory validation* that says "pending — no physical claim is made". The same statement is repeated on slide 6. The word "synthetic" appears twice on slide 3. |
| "Is the app actually built?" | Was unanswered in the first draft. | **Changed:** slide 3 now carries an explicit line — *built and tested today: the measurement engine, its benchmark and the validation tooling; the Android client is the implementation target of this proposal, not a finished product.* |
| "0 false positives — nonsense." | Would have been fatal if stated bare. | The deck states it with its denominator and population: "0 false-clear of 4 undersized; 0 false-accuse of 4 compliant", inside the synthetic card. No absolute claim anywhere. |
| "What happens on a curved pouch, which is most real packaging?" | The honest answer is a limitation. | Slide 4 answers it as risk #1 with the measured number (0.185 mm error with every gate green) and the consequence: out of scope, fixture-controlled, abstain. Slide 5 repeats "planar printed faces" as a deliberate limit. Admitting this reads as competence, not weakness. |
| "Does the tool decide guilt?" | Would be disqualifying in a regulatory context. | Reversed explicitly on slides 1, 2 and 5: *the officer records the legal determination*. Vocabulary is "candidate finding", "screening assistance", "evidence-linked" — never "verdict", "violation detected" or "court-admissible". |
| "They have not read the actual Rules." | Would undermine everything. | Slide 6 cites the Rules and the Act, and then names the genuinely open question — which glyphs and faces the rule counts — rather than pretending it is settled. |

## 2. What would confuse me?

| Confusion risk | Action taken |
|---|---|
| Eight workflow steps in a row is a lot to absorb | **Changed:** the first draft snaked left-right-down and was hard to follow. It is now two vertical tracks of four, with MEASURE and EVIDENCE emphasised and a single connector between tracks. |
| "Evidence-linked" is a phrase, not a picture | **Changed:** slide 5 gained a five-link chain diagram — finding → crop → raw + normalised value → rule version → engine version — so the phrase becomes concrete. |
| P1–P7 codes mean nothing to a non-specialist | They are never used as the *subject* of a sentence. Slide 3 says "P1–P7 acceptance criteria pre-registered and frozen"; slide 4 uses them only inside the stop-conditions block where each is immediately translated into plain English. |
| Uncertainty and guard bands are jargon | Always paired with plain wording: "millimetre estimate with an uncertainty interval", "measure or abstain". |

## 3. Which slide had unnecessary complexity?

Slide 3. The first draft put the technology table, the pipeline and the validation status on
one page with no visual hierarchy, and the panels were 30–40 % empty because they were
fixed-height. **Changed:** panels are now sized to their content, the pipeline reads as one
vertical spine ending in a two-way branch, and validation moved into three colour-coded
cards along the bottom so the green/amber distinction is visible in one glance.

## 4. Which claim looked unsupported?

Three, all fixed before output:

1. *"0.008 mm accuracy"* read as a product capability. Now qualified as **max arithmetic
   error on ideal renders**, inside the synthetic card.
2. *Android/OCR/rule-pack stack* read as existing software. Now under the template's own
   heading *Technologies to be **used***, with the build-status line added.
3. *Impact bullets* originally implied efficiency gains. Now explicitly closed with "no
   time-saving, accuracy or cost figure is claimed: none has been measured in the field
   yet", and with a line naming what **will** be measured during the pilot.

## 5. Where did the team sound generic?

The first draft's innovation block listed "OCR, rule engine, PDF reports, dashboards" —
which is what every team writes. **Changed:** the innovation block now names only things a
reader cannot assume: an uncertainty interval attached to each figure, fail-closed gates
that run *before* a number is displayed, and coverage that is pre-registered and
hash-checked so nothing can be selected after a result is seen. The differentiation is
stated as a documented system design, never as "no one else does this".

## 6. Where is the innovation obvious?

Slide 3's pipeline, at the branch. Every other compliance-scanning deck ends its flow at
"result". This one ends at **MEASURE / ABSTAIN → OFFICER REVIEW**. A reviewer who reads
nothing else takes away one idea: *this system is built to refuse.* The “Don’t guess.” band
on slide 2 states it in three words.

## 7. Residual risks accepted

| Risk | Why accepted |
|---|---|
| The deck is text-dense by modern design standards | SIH screening is read, not watched. The reference winning deck is denser still. Density is organised into titled panels with one question per slide. |
| No product screenshot | Faking one is worse. The workflow and evidence-chain diagrams carry that load. |
| Physical validation is pending, and an evaluator may weigh that down | It occupies one card of fifteen content blocks — precise, not apologetic — and is offset by what *is* real: a reproducible engine, 352 tests, pre-registered criteria and a committed reference protocol. |
| Two metadata fields are placeholders | They are team-specific and must not be invented. |

## 8. Visual QA performed

- **Automated geometry pass:** 0 issues across 475 objects — no element outside the page,
  none below the content area, no line wider than its box (every line measured with the
  actual Adobe base-14 width tables used to wrap it).
- **Rasterised inspection:** all six slides rendered to PNG and reviewed. Layout balance,
  panel fill, alignment, colour use and whitespace checked; content fill per slide is
  64–80 % of the content area, with no panel left visibly empty.
- **Consistency:** two fonts only (Times New Roman bold for titles, Arial for body), five
  colours plus greys, one bullet style, one chip style, one arrow style.
- **File validation:** PPTX — 23 parts, all XML well-formed, zip CRC clean, 6 slides, no
  flattened images. PDF — 6 pages, valid xref with all 17 offsets pointing at their
  objects, correct `%%EOF`.
- **Editability:** every diagram is composed of native preset shapes (`rect`, `roundRect`,
  `ellipse`, `rightArrow`, `downArrow`) with live text runs. Nothing is a picture.
