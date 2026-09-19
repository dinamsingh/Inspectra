"""Tests for the B6 equipment / access inventory gate.

These test the **inventory logic only**.  No test claims any instrument exists, none
uses physical data, and none touches a criterion.  `complete()` is a hypothetical
fully-equipped inventory, used to prove the gate is reachable — a gate that can only
ever say NO would be a bug, as the P7 memo already established.
"""
from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import validate_inventory as vi                   # noqa: E402
import verify_b2_setup as vbs                     # noqa: E402
import validate_flatness as vf                    # noqa: E402

from p0.core import dump_json, load_json          # noqa: E402


def record(item_type, unit=1, **over):
    spec = vi.CATALOGUE[item_type]
    rec = {
        "item_type": item_type,
        "item_id": "%s-%d" % (item_type, unit),
        "make_model": "some make, some model",
        "serial": "SN-%s-%d" % (item_type, unit),
        "availability": vi.AVAILABLE,
        "access_route": (spec["access_routes"][0] if spec["access_routes"] else None),
        "instrument_cal_ref": ("CERT-%s" % item_type
                               if spec["needs_cal_record"] else None),
        "certificate_ref": None,
        "operator": "OP1",
        "trained_operator": ("OP2 trained 2026-01-01"
                             if spec["needs_trained_operator"] else None),
        "verified_by": "OP1",
        "verified_at": "2026-01-01T00:00:00Z",
        "verification_status": "PHYSICALLY_INSPECTED",
        "notes": "",
    }
    rec.update(over)
    return rec


def complete(**over):
    """A hypothetical fully-equipped inventory.  Not a claim that it exists."""
    items = []
    for itype in sorted(vi.CATALOGUE):
        spec = vi.CATALOGUE[itype]
        if spec["required_level"] != vi.MANDATORY:
            continue
        for n in range(1, spec["min_quantity"] + 1):
            items.append(record(itype, unit=n))
    inv = {"recorded_by": "OP1", "recorded_at": "2026-01-01T00:00:00Z",
           "items": items}
    inv.update(over)
    return inv


def codes(issues, severity="ERROR"):
    return sorted(i["code"] for i in issues if i["severity"] == severity)


def verdict(inv, ev=None, reg=None):
    _i, summary = vi.validate(inv, ev, reg)
    return summary["verified"]


def drop(inv, item_type):
    inv = dict(inv)
    inv["items"] = [r for r in inv["items"] if r["item_type"] != item_type]
    return inv


def first(inv, item_type):
    for r in inv["items"]:
        if r["item_type"] == item_type:
            return r
    raise KeyError(item_type)


# ---------------------------------------------------------------------------
# catalogue provenance
# ---------------------------------------------------------------------------

class TestCatalogue(unittest.TestCase):
    def test_every_entry_names_a_purpose_and_a_blocker(self):
        for itype, spec in vi.CATALOGUE.items():
            self.assertTrue(spec["purpose"], itype)
            self.assertTrue(spec["blockers"], itype)

    def test_levels_are_from_the_documented_vocabulary(self):
        for itype, spec in vi.CATALOGUE.items():
            self.assertIn(spec["required_level"],
                          (vi.MANDATORY, vi.PREFERRED, vi.OPTIONAL), itype)

    def test_mandatory_set_matches_the_catalogue(self):
        self.assertEqual(
            set(vi.MANDATORY_TYPES),
            {k for k, v in vi.CATALOGUE.items()
             if v["required_level"] == vi.MANDATORY})

    def test_the_microscope_is_mandatory_not_preferred(self):
        """§13 files it under PREFERRED; its own MISSING row makes it binding."""
        self.assertEqual(vi.CATALOGUE["MEASURING_MICROSCOPE"]["required_level"],
                         vi.MANDATORY)
        self.assertTrue(vi.CATALOGUE["MEASURING_MICROSCOPE"]["needs_cal_record"])
        self.assertTrue(vi.CATALOGUE["MEASURING_MICROSCOPE"]["needs_trained_operator"])

    def test_two_phones_are_required_by_the_design(self):
        self.assertEqual(vi.CATALOGUE["PHONE"]["min_quantity"], 2)

    def test_calibration_records_are_demanded_exactly_where_documented(self):
        need = {k for k, v in vi.CATALOGUE.items() if v["needs_cal_record"]}
        self.assertEqual(need, {"LENGTH_STANDARD", "MEASURING_MICROSCOPE", "CALIPER"})

    def test_optional_items_never_appear_mandatory(self):
        for itype in ("CMM_OR_COMPARATOR", "RAW_CAPABLE_PHONE",
                      "DIAL_INDICATOR_SURFACE_PLATE"):
            self.assertEqual(vi.CATALOGUE[itype]["required_level"], vi.OPTIONAL)

    def test_no_item_is_invented_beyond_the_documented_bill_of_materials(self):
        """A guard against the catalogue growing equipment nobody asked for."""
        self.assertEqual(len(vi.CATALOGUE), 20)
        self.assertEqual(len(vi.MANDATORY_TYPES), 14)


# ---------------------------------------------------------------------------
# gate behaviour
# ---------------------------------------------------------------------------

class TestGateReachability(unittest.TestCase):
    def test_a_complete_inventory_returns_yes(self):
        issues, summary = vi.validate(complete())
        self.assertEqual(codes(issues), [])
        self.assertTrue(summary["verified"])
        self.assertEqual(summary["mandatory_ok"], summary["mandatory_types"])

    def test_the_blank_template_returns_no(self):
        self.assertFalse(verdict(vi.template()))

    def test_the_template_contains_every_mandatory_type(self):
        types = {r["item_type"] for r in vi.template()["items"]}
        for t in vi.MANDATORY_TYPES:
            self.assertIn(t, types)

    def test_verification_is_deterministic(self):
        self.assertEqual(vi.validate(complete()), vi.validate(complete()))

    def test_an_inventory_without_items_is_refused_outright(self):
        with self.assertRaises(vi.InventoryError):
            vi.validate({})

    def test_the_verdict_states_its_own_scope(self):
        _i, summary = vi.validate(complete())
        self.assertIn("does NOT mean B2 is closed", summary["scope"])


class TestNothingIsAssumed(unittest.TestCase):
    def test_an_absent_mandatory_item_is_no(self):
        for itype in vi.MANDATORY_TYPES:
            inv = drop(complete(), itype)
            issues, summary = vi.validate(inv)
            self.assertIn("MANDATORY_ITEM_ABSENT", codes(issues), itype)
            self.assertFalse(summary["verified"], itype)

    def test_unknown_availability_is_no(self):
        for av in (vi.UNKNOWN, vi.ACCESS_NEEDED, vi.NOT_AVAILABLE):
            inv = complete()
            first(inv, "FLATBED_SCANNER")["availability"] = av
            issues, summary = vi.validate(inv)
            self.assertIn("ITEM_NOT_AVAILABLE", codes(issues), av)
            self.assertFalse(summary["verified"], av)

    def test_a_missing_availability_field_is_rejected(self):
        inv = complete()
        first(inv, "COPY_STAND")["availability"] = None
        issues, _s = vi.validate(inv)
        self.assertIn("BAD_AVAILABILITY", codes(issues))

    def test_an_invented_availability_value_is_rejected(self):
        inv = complete()
        first(inv, "COPY_STAND")["availability"] = "PROBABLY"
        issues, _s = vi.validate(inv)
        self.assertIn("BAD_AVAILABILITY", codes(issues))

    def test_available_without_evidence_does_not_count(self):
        for field in ("item_id", "make_model", "verified_by", "verified_at"):
            inv = complete()
            first(inv, "LIGHTING")[field] = None
            issues, summary = vi.validate(inv)
            self.assertFalse(summary["verified"], field)
            self.assertTrue({"EVIDENCE_INCOMPLETE", "QUANTITY_SHORT"}
                            & set(codes(issues)), field)

    def test_placeholder_strings_are_not_evidence(self):
        for bad in ("TBD", "unknown", "n/a", "", "  ", "UNSPECIFIED"):
            inv = complete()
            first(inv, "BACKING_PLATE")["make_model"] = bad
            issues, summary = vi.validate(inv)
            self.assertFalse(summary["verified"], bad)
            self.assertIn("EVIDENCE_INCOMPLETE", codes(issues), bad)

    def test_a_missing_calibration_record_is_no_where_mandatory(self):
        for itype in ("LENGTH_STANDARD", "MEASURING_MICROSCOPE", "CALIPER"):
            inv = complete()
            first(inv, itype)["instrument_cal_ref"] = None
            issues, summary = vi.validate(inv)
            self.assertFalse(summary["verified"], itype)
            self.assertIn("EVIDENCE_INCOMPLETE", codes(issues), itype)

    def test_a_calibration_record_is_not_demanded_where_undocumented(self):
        inv = complete()
        first(inv, "COPY_STAND")["instrument_cal_ref"] = None
        self.assertTrue(verdict(inv))

    def test_an_untrained_microscope_operator_is_no(self):
        inv = complete()
        first(inv, "MEASURING_MICROSCOPE")["trained_operator"] = None
        issues, summary = vi.validate(inv)
        self.assertFalse(summary["verified"])
        self.assertIn("EVIDENCE_INCOMPLETE", codes(issues))

    def test_one_phone_is_an_inventory_failure_not_a_silent_downgrade(self):
        inv = complete()
        inv["items"] = [r for r in inv["items"]
                        if not (r["item_type"] == "PHONE" and r["item_id"].endswith("2"))]
        issues, summary = vi.validate(inv)
        self.assertIn("QUANTITY_SHORT", codes(issues))
        self.assertFalse(summary["verified"])
        detail = " ".join(i["detail"] for i in issues)
        self.assertIn("P4", detail)

    def test_the_same_object_listed_twice_does_not_fill_a_quantity(self):
        inv = complete()
        phones = [r for r in inv["items"] if r["item_type"] == "PHONE"]
        phones[1]["item_id"] = phones[0]["item_id"]
        issues, summary = vi.validate(inv)
        self.assertIn("DUPLICATE_ITEM_ID", codes(issues))
        self.assertFalse(summary["verified"])

    def test_an_item_outside_the_catalogue_is_rejected(self):
        inv = complete()
        rogue = record("FLATBED_SCANNER")
        rogue["item_type"] = "LASER_TRACKER"
        inv["items"].append(rogue)
        issues, _s = vi.validate(inv)
        self.assertIn("UNKNOWN_ITEM_TYPE", codes(issues))

    def test_a_non_object_item_is_rejected(self):
        inv = complete()
        inv["items"].append("a ruler")
        issues, _s = vi.validate(inv)
        self.assertIn("BAD_ITEM_RECORD", codes(issues))


class TestPreferredAndOptionalNeverBlock(unittest.TestCase):
    def test_preferred_items_absent_only_warn(self):
        issues, summary = vi.validate(complete())
        self.assertTrue(summary["verified"])
        self.assertIn("PREFERRED_ITEM_ABSENT", codes(issues, "WARN"))

    def test_optional_items_absent_are_silent(self):
        issues, _s = vi.validate(complete())
        detail = " ".join(i["detail"] for i in issues)
        self.assertNotIn("CMM_OR_COMPARATOR", detail)

    def test_adding_a_preferred_item_clears_its_warning(self):
        inv = complete()
        inv["items"].append(record("CLAMPS_OR_VACUUM"))
        issues, summary = vi.validate(inv)
        self.assertTrue(summary["verified"])
        warns = " ".join(i["detail"] for i in issues if i["severity"] == "WARN")
        self.assertNotIn("CLAMPS_OR_VACUUM", warns)


class TestCrossChecksAvoidASecondSourceOfTruth(unittest.TestCase):
    def _b2(self, **over):
        ev = vbs.template()
        ev["scanner"]["instrument_id"] = "FLATBED_SCANNER-1"
        ev["length_standard"]["standard_id"] = "LENGTH_STANDARD-1"
        ev["microscope"]["instrument_id"] = "MEASURING_MICROSCOPE-1"
        ev["caliper"]["instrument_id"] = "CALIPER-1"
        ev["printing"]["printer_id"] = "PRINTER-1"
        for section, field_value in over.items():
            ev[section].update(field_value)
        return ev

    def test_matching_ids_are_clean(self):
        issues, summary = vi.validate(complete(), self._b2())
        self.assertEqual(codes(issues), [])
        self.assertTrue(summary["verified"])

    def test_a_disagreeing_scanner_id_is_rejected(self):
        ev = self._b2(scanner={"instrument_id": "SOME-OTHER-SCANNER"})
        issues, summary = vi.validate(complete(), ev)
        self.assertIn("ID_DISAGREES_WITH_B2_EVIDENCE", codes(issues))
        self.assertFalse(summary["verified"])

    def test_every_cross_checked_item_is_compared(self):
        for section, field, itype in (
                ("scanner", "instrument_id", "FLATBED_SCANNER"),
                ("length_standard", "standard_id", "LENGTH_STANDARD"),
                ("microscope", "instrument_id", "MEASURING_MICROSCOPE"),
                ("caliper", "instrument_id", "CALIPER"),
                ("printing", "printer_id", "PRINTER")):
            ev = self._b2(**{section: {field: "MISMATCH"}})
            issues, _s = vi.validate(complete(), ev)
            self.assertIn("ID_DISAGREES_WITH_B2_EVIDENCE", codes(issues), itype)

    def test_a_blank_b2_evidence_file_does_not_invent_disagreement(self):
        issues, summary = vi.validate(complete(), vbs.template())
        self.assertEqual(codes(issues), [])
        self.assertTrue(summary["verified"])

    def test_a_backing_plate_used_but_not_inventoried_is_rejected(self):
        reg = vf.template()
        reg["panels"]["P01"]["backing_id"] = "SOME-PLATE"
        issues, summary = vi.validate(complete(), None, reg)
        self.assertIn("BACKING_PLATE_NOT_IN_INVENTORY", codes(issues))
        self.assertFalse(summary["verified"])

    def test_a_matching_backing_plate_is_clean(self):
        reg = vf.template()
        reg["panels"]["P01"]["backing_id"] = "BACKING_PLATE-1"
        issues, summary = vi.validate(complete(), None, reg)
        self.assertEqual(codes(issues), [])
        self.assertTrue(summary["verified"])


class TestSamplesAreNotEquipment(unittest.TestCase):
    def test_packaged_products_have_no_catalogue_entry(self):
        for bad in ("BISCUIT_PACK", "PEANUT_BUTTER_JAR", "ROOM_FRESHENER",
                    "CREATINE_TUB", "PACKAGED_PRODUCT", "SAMPLE"):
            self.assertNotIn(bad, vi.CATALOGUE)

    def test_a_product_recorded_as_equipment_is_rejected(self):
        inv = complete()
        rogue = record("FLATBED_SCANNER")
        rogue["item_type"] = "BISCUIT_PACK"
        inv["items"].append(rogue)
        issues, summary = vi.validate(inv)
        self.assertIn("UNKNOWN_ITEM_TYPE", codes(issues))
        self.assertFalse(summary["verified"])


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _cli(self, argv):
        buf = io.StringIO()
        old_o, old_e = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf, buf
        try:
            rc = vi.main(argv)
        finally:
            sys.stdout, sys.stderr = old_o, old_e
        return rc, buf.getvalue()

    def test_template_then_verify_is_no(self):
        p = os.path.join(self.tmp, "inv.json")
        self.assertEqual(self._cli(["--template", p])[0], 0)
        rc, txt = self._cli(["--inventory", p])
        self.assertEqual(rc, 1)
        self.assertIn("B6_INVENTORY_VERIFIED = NO", txt)

    def test_a_complete_inventory_exits_zero(self):
        p = os.path.join(self.tmp, "ok.json")
        dump_json(p, complete())
        rc, txt = self._cli(["--inventory", p])
        self.assertEqual(rc, 0)
        self.assertIn("B6_INVENTORY_VERIFIED = YES", txt)
        self.assertIn("does NOT mean B2 is closed", txt)

    def test_missing_file_exits_two(self):
        rc, txt = self._cli(["--inventory", os.path.join(self.tmp, "nope.json")])
        self.assertEqual(rc, 2)
        self.assertIn("B6_INVENTORY_VERIFIED = NO", txt)

    def test_json_out_records_the_verdict(self):
        p = os.path.join(self.tmp, "ok.json")
        out = os.path.join(self.tmp, "res.json")
        dump_json(p, complete())
        self._cli(["--inventory", p, "--json-out", out])
        got = load_json(out)
        self.assertEqual(got["B6_INVENTORY_VERIFIED"], "YES")
        self.assertTrue(got["summary"]["verified"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
