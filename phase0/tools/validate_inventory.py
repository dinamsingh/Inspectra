#!/usr/bin/env python3
"""Physical equipment / access inventory gate (blocker B6).

`P0_EXECUTION_PLAN.md` §12 states what B6 needs: *"the §13 inventory completed with
real yes/no answers and substitutes agreed for anything missing"*.  This tool is that
inventory, made machine-checkable.

**It deliberately does not duplicate the other gates.**  Three files, three jobs, one
source of truth each:

* **this inventory** — does the physical resource *exist*, is it *identified*, and is
  its *paperwork* on hand;
* `tools/verify_b2_setup.py` — the reference tier's *capability* (optical dpi, bit
  depth, reflected illumination, both-axis calibration, ...);
* `tools/validate_flatness.py` — the *measurements* taken with the B4 instruments.

Where an item appears in more than one place, this tool **cross-checks the ids** so a
second source of truth cannot open up: an inventory scanner id that differs from the
B2 evidence scanner id is an error, not two opinions.

Nothing is inferred.  An item is only available when it says `AVAILABLE` *and* carries
the evidence its catalogue entry demands.  `UNKNOWN`, `ACCESS_NEEDED`, a placeholder
string or a missing record all read as not available, which is the safe default.

Scope warning, enforced in the output: a `YES` here means **equipment is on hand**.  It
does not mean B2 is closed, B4 is closed, or anything has been validated.

Usage:
    python3 tools/validate_inventory.py --template reference/equipment_inventory.json
    python3 tools/validate_inventory.py --inventory reference/equipment_inventory.json
    python3 tools/validate_inventory.py --inventory <inv> --b2-evidence <ev> \
            --flatness-register <reg>
Exit code: 0 verified, 1 not verified, 2 could not load.
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.core import dump_json, load_json          # noqa: E402

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"

MANDATORY, PREFERRED, OPTIONAL = "MANDATORY", "PREFERRED", "OPTIONAL"

AVAILABLE, NOT_AVAILABLE = "AVAILABLE", "NOT_AVAILABLE"
UNKNOWN, ACCESS_NEEDED = "UNKNOWN", "ACCESS_NEEDED"
AVAILABILITY = (AVAILABLE, NOT_AVAILABLE, UNKNOWN, ACCESS_NEEDED)

# Access routes, as classified in B2_MINIMUM_SETUP.md §9 and B6_EQUIPMENT_INVENTORY.md.
# These are route *classifications*, not claims that any particular place has the item.
BORROW = "CAN_BORROW"
COLLEGE = "COLLEGE_LAB"
METROLOGY = "SPECIALIST_METROLOGY_LAB"
PRINTSHOP = "PRINT_OR_REPROGRAPHICS_SHOP"
CHEAP = "CAN_PURCHASE_CHEAPLY"
SOFTWARE = "SOFTWARE_ONLY"

PLACEHOLDERS = frozenset(("", "-", "?", "n/a", "na", "tbd", "todo", "none", "null",
                          "unknown", "unspecified", "pending", "xxx"))


def _item(item_type, purpose, blockers, level, quantity=1, cal_record=False,
          trained_operator=False, access=(), cross_check=None, note=""):
    return {"item_type": item_type, "purpose": purpose, "blockers": tuple(blockers),
            "required_level": level, "min_quantity": quantity,
            "needs_cal_record": cal_record,
            "needs_trained_operator": trained_operator,
            "access_routes": tuple(access), "cross_check": cross_check, "note": note}


# The catalogue is derived from the documents, not invented: P0_PROTOCOL.md §0 (bill of
# materials) and §1 step 6, P0_EXECUTION_PLAN.md §13, B2_MINIMUM_SETUP.md §1/§9,
# B2_SETUP_VERIFICATION.md §1-§3, B4_FLATNESS_CONTROL.md §4/§11.
CATALOGUE = {
    "FLATBED_SCANNER": _item(
        "FLATBED_SCANNER", "primary reference measurement of every measured glyph",
        ("B2",), MANDATORY, access=(BORROW, COLLEGE, PRINTSHOP),
        cross_check=("scanner", "instrument_id"),
        note="capability (2400 dpi optical, 8-bit grey, enhancement off) is checked by "
             "verify_b2_setup.py, not here"),
    "LENGTH_STANDARD": _item(
        "LENGTH_STANDARD", "calibrates the scanner scale in both axes",
        ("B2",), MANDATORY, cal_record=True, access=(METROLOGY,),
        cross_check=("length_standard", "standard_id"),
        note="unconditional since S3 = NO; an uncertified ruler is not a substitute"),
    "MEASURING_MICROSCOPE": _item(
        "MEASURING_MICROSCOPE",
        "the only independent realisation of the measurand; P1 depends on it",
        ("B2",), MANDATORY, cal_record=True, trained_operator=True,
        access=(METROLOGY,), cross_check=("microscope", "instrument_id"),
        note="P0_EXECUTION_PLAN.md §13 lists it under PREFERRED, but the same table and "
             "its MISSING row state that without it P1 is uncomputable and NO accuracy "
             "claim may be made. The stronger statement is binding, so it is MANDATORY "
             "here"),
    "CALIPER": _item(
        "CALIPER", "frame survey, the 100 mm print check, and the B3 registration",
        ("B2", "B3", "B4", "CAPTURE"), MANDATORY, cal_record=True,
        access=(BORROW, COLLEGE), cross_check=("caliper", "instrument_id"),
        note="never a glyph reference (P0_EXECUTION_PLAN.md §2.3)"),
    "STRAIGHTEDGE": _item(
        "STRAIGHTEDGE", "flatness gap measurement across both window spans",
        ("B4",), MANDATORY, access=(BORROW, CHEAP)),
    "GAP_GAUGE": _item(
        "GAP_GAUGE",
        "reads the straightedge gap; feeler set, or a dial indicator on a surface plate",
        ("B4",), MANDATORY, access=(BORROW, COLLEGE, CHEAP),
        note="must resolve better than the 0.262 mm short-span acceptance; the "
             "resolution itself is checked by validate_flatness.py"),
    "BACKING_PLATE": _item(
        "BACKING_PLATE", "defines the flat print plane; >= 150 x 100 mm",
        ("B4", "CAPTURE"), MANDATORY, access=(BORROW, CHEAP),
        note="its own flatness must be verified, which is what makes this a B6 item"),
    "FIDUCIAL_FRAME_STOCK": _item(
        "FIDUCIAL_FRAME_STOCK",
        "dimensionally stable stock for the four-marker frame",
        ("CAPTURE", "CALIBRATION"), MANDATORY, access=(CHEAP, PRINTSHOP)),
    "PRINT_STOCK": _item(
        "PRINT_STOCK", "coupon substrate", ("B2", "CAPTURE"), MANDATORY,
        access=(CHEAP, PRINTSHOP)),
    "PRINTER": _item(
        "PRINTER", "prints the coupons and the frame at true 100 % scale",
        ("B2", "CAPTURE"), MANDATORY, access=(BORROW, PRINTSHOP),
        cross_check=("printing", "printer_id")),
    "PHONE": _item(
        "PHONE", "the device under test; AF/AE/AWB lock, HDR off",
        ("CAPTURE",), MANDATORY, quantity=2, access=(BORROW,),
        note="P0_EXECUTION_PLAN.md §13 MISSING: with one phone, verdict #24 and "
             "criterion P4 become uncomputable and the claim is per-device only. That "
             "is a design change, so one phone is an inventory failure here, not a "
             "silent downgrade"),
    "COPY_STAND": _item(
        "COPY_STAND", "holds the camera still for a 7-frame burst",
        ("CAPTURE",), MANDATORY, access=(BORROW, CHEAP)),
    "LIGHTING": _item(
        "LIGHTING", "two diffuse sources at ~45 deg, no specular path",
        ("CAPTURE",), MANDATORY, access=(BORROW, CHEAP)),
    "CONVERSION_TOOL": _item(
        "CONVERSION_TOOL", "phone output -> 8-bit greyscale PNG with no sharpening",
        ("CAPTURE",), MANDATORY, access=(SOFTWARE,),
        note="A-02; verify_b2_setup.py records that the conversion was verified, this "
             "records which tool and version did it"),
    # --- preferred / optional: reported, never blocking -------------------
    "SECOND_PRINT_STOCK": _item(
        "SECOND_PRINT_STOCK", "matte / semi-gloss print variation block",
        ("CAPTURE",), PREFERRED, access=(CHEAP,)),
    "CLAMPS_OR_VACUUM": _item(
        "CLAMPS_OR_VACUUM", "holds coupons flat instead of relying on adhesive",
        ("B4",), PREFERRED, access=(BORROW, CHEAP)),
    "CROSSED_POLARISERS": _item(
        "CROSSED_POLARISERS", "glare control on glossy stock",
        ("CAPTURE",), PREFERRED, access=(CHEAP,)),
    "DIAL_INDICATOR_SURFACE_PLATE": _item(
        "DIAL_INDICATOR_SURFACE_PLATE",
        "a more quantitative flatness check than a straight edge",
        ("B4",), OPTIONAL, access=(METROLOGY, COLLEGE)),
    "CMM_OR_COMPARATOR": _item(
        "CMM_OR_COMPARATOR", "frame survey alternative; not a blocker",
        ("CALIBRATION",), OPTIONAL, access=(METROLOGY,),
        note="the caliper survey already contributes ~0.0006 mm on a 3 mm glyph"),
    "RAW_CAPABLE_PHONE": _item(
        "RAW_CAPABLE_PHONE", "would let the RAW vs JPEG verdict be tested",
        ("CAPTURE",), OPTIONAL, access=(BORROW,)),
}

MANDATORY_TYPES = tuple(sorted(k for k, v in CATALOGUE.items()
                               if v["required_level"] == MANDATORY))


class InventoryError(Exception):
    pass


def named(value):
    return isinstance(value, str) and value.strip().lower() not in PLACEHOLDERS


def evidence_fields(spec):
    """What must be filled in for this item to count as available."""
    fields = ["item_id", "make_model", "verified_by", "verified_at"]
    if spec["needs_cal_record"]:
        fields.append("instrument_cal_ref")
    if spec["needs_trained_operator"]:
        fields.append("trained_operator")
    return fields


def validate(inventory, b2_evidence=None, flatness_register=None):
    issues = []

    def add(sev, code, detail, where=None):
        issues.append({"severity": sev, "code": code, "where": where,
                       "detail": detail})

    items = inventory.get("items")
    if not isinstance(items, list):
        raise InventoryError("the inventory must carry an `items` list")

    by_type = {}
    for rec in items:
        if not isinstance(rec, dict):
            add(ERROR, "BAD_ITEM_RECORD", "every item must be an object")
            continue
        itype = rec.get("item_type")
        if itype not in CATALOGUE:
            add(ERROR, "UNKNOWN_ITEM_TYPE",
                "item_type=%r is not in the protocol's catalogue; the inventory may "
                "not invent equipment the protocol does not require" % (itype,),
                rec.get("item_id"))
            continue
        by_type.setdefault(itype, []).append(rec)

    available, status = {}, {}
    for itype in sorted(CATALOGUE):
        spec = CATALOGUE[itype]
        recs = by_type.get(itype, [])
        ok = []
        for rec in recs:
            iid = rec.get("item_id")
            av = rec.get("availability")
            if av not in AVAILABILITY:
                add(ERROR, "BAD_AVAILABILITY",
                    "availability=%r must be one of %s" % (av, list(AVAILABILITY)),
                    iid)
                continue
            if av != AVAILABLE:
                if spec["required_level"] == MANDATORY:
                    add(ERROR, "ITEM_NOT_AVAILABLE",
                        "%s is %s; a mandatory resource is only counted when it is "
                        "%s with evidence" % (itype, av, AVAILABLE), iid)
                continue
            missing = [f for f in evidence_fields(spec)
                       if not named(str(rec.get(f)) if rec.get(f) is not None else None)]
            if missing:
                add(ERROR, "EVIDENCE_INCOMPLETE",
                    "%s claims %s but is missing %s; availability without evidence is "
                    "not availability" % (itype, AVAILABLE, sorted(missing)), iid)
                continue
            if spec["needs_cal_record"] and not named(rec.get("instrument_cal_ref")):
                add(ERROR, "CALIBRATION_RECORD_MISSING",
                    "%s requires a calibration record reference" % itype, iid)
                continue
            ok.append(rec)
        available[itype] = ok
        if not recs:
            status[itype] = "ABSENT"
            if spec["required_level"] == MANDATORY:
                add(ERROR, "MANDATORY_ITEM_ABSENT",
                    "%s has no inventory record at all. Nothing is assumed to exist"
                    % itype)
            elif spec["required_level"] == PREFERRED:
                add(WARN, "PREFERRED_ITEM_ABSENT",
                    "%s is absent; it materially strengthens the result but does not "
                    "block" % itype)
        elif len(ok) >= spec["min_quantity"]:
            status[itype] = "OK"
        else:
            status[itype] = "SHORT"
            if spec["required_level"] == MANDATORY:
                add(ERROR, "QUANTITY_SHORT",
                    "%s needs %d verified unit(s), %d recorded. %s"
                    % (itype, spec["min_quantity"], len(ok), spec["note"] or ""))

        ids = [r.get("item_id") for r in recs if named(r.get("item_id"))]
        if len(set(ids)) != len(ids):
            add(ERROR, "DUPLICATE_ITEM_ID",
                "%s lists the same item_id twice; two records for one physical object "
                "inflate the count" % itype)

    # --- cross-checks against the other gates ----------------------------
    if b2_evidence is not None:
        for itype, spec in sorted(CATALOGUE.items()):
            cc = spec["cross_check"]
            if not cc or not available.get(itype):
                continue
            sec = b2_evidence.get(cc[0]) or {}
            other = sec.get(cc[1])
            if not named(other):
                continue
            mine = {r.get("item_id") for r in available[itype]}
            if other not in mine:
                add(ERROR, "ID_DISAGREES_WITH_B2_EVIDENCE",
                    "the B2 evidence names %s=%r for %s but the inventory has %s; one "
                    "physical instrument may not have two identities"
                    % (".".join(cc), other, itype, sorted(mine)))
    if flatness_register is not None:
        panels = flatness_register.get("panels") or {}
        plates = {p.get("backing_id") for p in panels.values()
                  if isinstance(p, dict) and named(p.get("backing_id"))}
        mine = {r.get("item_id") for r in available.get("BACKING_PLATE", [])}
        for plate in sorted(plates - mine):
            add(ERROR, "BACKING_PLATE_NOT_IN_INVENTORY",
                "the flatness register uses backing plate %r, which is not a verified "
                "inventory item" % plate)

    n_err = sum(1 for i in issues if i["severity"] == ERROR)
    mandatory_ok = all(status.get(t) == "OK" for t in MANDATORY_TYPES)
    summary = {
        "items_recorded": len(items),
        "mandatory_types": len(MANDATORY_TYPES),
        "mandatory_ok": sum(1 for t in MANDATORY_TYPES if status.get(t) == "OK"),
        "status_by_item": dict(sorted(status.items())),
        "issues": {sev: sum(1 for i in issues if i["severity"] == sev)
                   for sev in (ERROR, WARN, INFO)},
        "verified": bool(mandatory_ok and n_err == 0),
        "scope": ("equipment on hand only; this does NOT mean B2 is closed, B4 is "
                  "closed, or that anything has been validated"),
    }
    return issues, summary


def template():
    """A blank inventory: every mandatory item present as a record, all fields null."""
    items = []
    for itype in sorted(CATALOGUE):
        spec = CATALOGUE[itype]
        for n in range(spec["min_quantity"]):
            rec = {
                "item_type": itype,
                "item_id": None,
                "make_model": None,
                "serial": None,
                "availability": None,
                "access_route": None,
                "instrument_cal_ref": None,
                "certificate_ref": None,
                "operator": None,
                "trained_operator": None,
                "verified_by": None,
                "verified_at": None,
                "verification_status": None,
                "notes": "",
                "_required_level": spec["required_level"],
                "_blockers": list(spec["blockers"]),
                "_purpose": spec["purpose"],
                "_access_routes": list(spec["access_routes"]),
            }
            if spec["min_quantity"] > 1:
                rec["_unit"] = n + 1
            items.append(rec)
    return {
        "_README": [
            "B6 equipment / access inventory.  One record per physical object.",
            "Nothing is assumed to exist: availability must read AVAILABLE and the",
            "evidence fields must be filled, or the item does not count.",
            "UNKNOWN and ACCESS_NEEDED are honest answers and both read as NO.",
            "Packaged products are SAMPLES, not measurement equipment, and are not",
            "inventory items.",
            "Capability lives in verify_b2_setup.py; flatness measurements live in",
            "validate_flatness.py.  This file records existence and paperwork only.",
        ],
        "recorded_by": None,
        "recorded_at": None,
        "items": items,
    }


def report(issues, summary, out=None):
    out = out or sys.stdout
    for itype in sorted(summary["status_by_item"]):
        spec = CATALOGUE[itype]
        out.write("  %-30s %-7s %-10s %s\n"
                  % (itype, summary["status_by_item"][itype], spec["required_level"],
                     "/".join(spec["blockers"])))
    out.write("  mandatory verified: %d of %d\n"
              % (summary["mandatory_ok"], summary["mandatory_types"]))
    out.write("  issues: %s\n" % summary["issues"])
    for i in issues:
        out.write("  [%s] %-34s %s%s\n"
                  % (i["severity"], i["code"],
                     ("%s " % i["where"]) if i["where"] else "", i["detail"]))
    out.write("  scope: %s\n" % summary["scope"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory")
    ap.add_argument("--template")
    ap.add_argument("--b2-evidence")
    ap.add_argument("--flatness-register")
    ap.add_argument("--json-out")
    a = ap.parse_args(argv)

    if a.template:
        dump_json(a.template, template())
        sys.stdout.write("blank equipment inventory written: %s\n" % a.template)
        sys.stdout.write("%d mandatory item types, every field null, so verification "
                         "returns NO until each one is real\n" % len(MANDATORY_TYPES))
        return 0
    if not a.inventory:
        ap.error("one of --inventory or --template is required")

    try:
        inv = load_json(a.inventory)
        ev = load_json(a.b2_evidence) if a.b2_evidence else None
        reg = load_json(a.flatness_register) if a.flatness_register else None
    except Exception as exc:                                    # noqa: BLE001
        sys.stderr.write("B6_INVENTORY_VERIFIED = NO (%s)\n" % exc)
        return 2

    try:
        issues, summary = validate(inv, ev, reg)
    except InventoryError as exc:
        sys.stderr.write("B6_INVENTORY_VERIFIED = NO (%s)\n" % exc)
        return 2

    sys.stdout.write("inventory: %s\n" % a.inventory)
    report(issues, summary)
    if a.json_out:
        dump_json(a.json_out, {"summary": summary, "issues": issues,
                               "B6_INVENTORY_VERIFIED": "YES" if summary["verified"]
                               else "NO"})
    sys.stdout.write("B6_INVENTORY_VERIFIED = %s\n"
                     % ("YES" if summary["verified"] else "NO"))
    return 0 if summary["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
