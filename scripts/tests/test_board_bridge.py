"""Tests for the board bridge (specification section 22, A11)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from board_bridge import Board, BridgeError, Field, parse_changes, run  # noqa: E402

CONFIG = {"organization": {"projectV2": {
    "id": "PVT_1", "title": "VPS Configuration", "url": "https://github.com/orgs/Pivot-Softwares/projects/1",
    "fields": {"nodes": [
        {"id": "F_TITLE", "name": "Title", "dataType": "TITLE"},
        {"id": "F_STATUS", "name": "Status", "dataType": "SINGLE_SELECT",
         "options": [{"id": "o_backlog", "name": "Backlog"}, {"id": "o_ready", "name": "Ready"}]},
        {"id": "F_SPRINT", "name": "Sprint", "dataType": "ITERATION",
         "configuration": {"duration": 14, "startDay": 1,
                           "iterations": [{"id": "i_1", "title": "Sprint 1", "startDate": "2026-10-06", "duration": 14}],
                           "completedIterations": []}},
        {"id": "F_POINTS", "name": "Story Points", "dataType": "NUMBER"},
        {"id": "F_START", "name": "Start date", "dataType": "DATE"},
        {},
    ]},
    "views": {"nodes": [{"id": "V_1", "number": 1, "name": "Product backlog", "layout": "TABLE_LAYOUT",
                         "filter": "is:open"}]},
}}}
ITEMS = {"node": {"items": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": [
    {"id": "PVTI_12", "content": {"number": 12}, "fieldValues": {"nodes": [
        {"name": "Backlog", "field": {"name": "Status"}},
        {"number": 3.0, "field": {"name": "Story Points"}},
        {"text": "Task: one", "field": {"name": "Title"}},
        {},
    ]}},
    {"id": "PVTI_DRAFT", "content": {}, "fieldValues": {"nodes": []}},
]}}}


class FakeGh:
    """Answers the bridge's gh calls from fixtures and records every call."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, *arguments: str) -> str:
        self.calls.append(arguments)
        if arguments[:2] == ("api", "repos/Pivot-Softwares/VPS-Configuration/issues/13"):
            return json.dumps({"node_id": "I_13"})
        query = next(argument for argument in arguments if argument.startswith("query="))
        if "organization(login" in query:
            return json.dumps({"data": CONFIG})
        if "items(first" in query:
            return json.dumps({"data": ITEMS})
        if "addProjectV2ItemById" in query:
            return json.dumps({"data": {"addProjectV2ItemById": {"item": {"id": "PVTI_13"}}}})
        return json.dumps({"data": {}})

    def mutations(self) -> list[tuple[str, ...]]:
        return [call for call in self.calls if any("updateProjectV2ItemFieldValue" in a or "clearProjectV2" in a
                                                   for a in call)]


def board(gh: FakeGh) -> Board:
    return Board("Pivot-Softwares", 1, "Pivot-Softwares/VPS-Configuration", gh)


class FieldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fields = board(FakeGh()).fields

    def test_choices_include_options_and_iterations(self) -> None:
        self.assertEqual(self.fields["Status"].resolve("Ready"), "o_ready")
        self.assertEqual(self.fields["Sprint"].resolve("Sprint 1"), "i_1")

    def test_values_are_checked_by_type(self) -> None:
        for name, value in (("Status", "Doing"), ("Story Points", "3"), ("Story Points", True),
                            ("Start date", "next week"), ("Title", "x")):
            with self.subTest(name=name, value=value), self.assertRaises(BridgeError):
                self.fields[name].resolve(value)
        self.assertEqual(self.fields["Start date"].resolve("2026-10-06"), "2026-10-06")
        self.assertIsNone(self.fields["Status"].resolve(None))

    def test_a_node_without_a_name_is_not_a_field(self) -> None:
        self.assertIsNone(Field.from_api({}))


class PayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fields = board(FakeGh()).fields

    def test_dry_run_is_the_default(self) -> None:
        dry_run, changes = parse_changes({"changes": [{"issue": 12, "field": "Status", "value": "Ready"}]},
                                         self.fields)
        self.assertTrue(dry_run)
        self.assertEqual(len(changes), 1)

    def test_invalid_payloads_are_rejected_before_writing(self) -> None:
        ready = {"issue": 12, "field": "Status", "value": "Ready"}
        payloads: tuple[dict, ...] = (
            {}, {"changes": []}, {"changes": [{"issue": 12, "field": "Status"}]},
            {"changes": [{"issue": "12", "field": "Status", "value": "Ready"}]},
            {"changes": [{"issue": 12, "field": "Owner", "value": "x"}]},
            {"changes": [ready], "dry_run": "no"}, {"changes": [ready], "extra": 1})
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(BridgeError):
                parse_changes(payload, self.fields)


class BoardTests(unittest.TestCase):
    def test_items_map_issue_numbers_to_field_values_and_skip_drafts(self) -> None:
        items = board(FakeGh()).items()
        self.assertEqual(list(items), [12])
        self.assertEqual(items[12]["fields"], {"Status": "Backlog", "Story Points": 3.0, "Title": "Task: one"})

    def test_dry_run_writes_nothing(self) -> None:
        gh = FakeGh()
        result = board(gh).set_fields({"changes": [{"issue": 12, "field": "Status", "value": "Ready"}]})
        self.assertEqual(result["changes"][0]["result"], "would set")
        self.assertEqual(gh.mutations(), [])

    def test_values_already_set_are_skipped(self) -> None:
        gh = FakeGh()
        result = board(gh).set_fields({"dry_run": False, "changes": [
            {"issue": 12, "field": "Status", "value": "Backlog"},
            {"issue": 12, "field": "Story Points", "value": 3}]})
        self.assertEqual([change["result"] for change in result["changes"]], ["skipped", "skipped"])
        self.assertEqual(gh.mutations(), [])

    def test_apply_adds_a_missing_issue_then_sets_and_clears(self) -> None:
        gh = FakeGh()
        result = board(gh).set_fields({"dry_run": False, "changes": [
            {"issue": 13, "field": "Sprint", "value": "Sprint 1"},
            {"issue": 12, "field": "Story Points", "value": None}]})
        self.assertEqual([change["result"] for change in result["changes"]], ["set", "set"])
        update, clear = gh.mutations()
        self.assertIn("item=PVTI_13", update)
        self.assertIn("value=i_1", update)
        self.assertIn("item=PVTI_12", clear)
        self.assertTrue(any("clearProjectV2ItemFieldValue" in argument for argument in clear))

    def test_numbers_are_sent_as_numbers(self) -> None:
        gh = FakeGh()
        board(gh).set_fields({"dry_run": False, "changes": [{"issue": 12, "field": "Story Points", "value": 5}]})
        (update,) = gh.mutations()
        self.assertEqual(update[update.index("value=5") - 1], "-F")

    def test_payload_values_never_become_part_of_the_query(self) -> None:
        gh = FakeGh()
        hostile = "Ready\") { x } mutation { deleteProjectV2(input: {}) }"
        with self.assertRaises(BridgeError):
            board(gh).set_fields({"dry_run": False, "changes": [{"issue": 12, "field": "Status", "value": hostile}]})
        self.assertEqual(gh.mutations(), [])


class RunTests(unittest.TestCase):
    def test_unknown_operations_are_refused(self) -> None:
        with self.assertRaises(BridgeError):
            run("delete-everything", {}, lambda: board(FakeGh()))

    def test_dump_config_and_read_items(self) -> None:
        config, passed = run("dump-config", {}, lambda: board(FakeGh()))
        self.assertTrue(passed)
        self.assertEqual(config["project"]["id"], "PVT_1")
        items, _ = run("read-items", {"issues": [99]}, lambda: board(FakeGh()))
        self.assertEqual(items, {"items": {}})


if __name__ == "__main__":
    unittest.main()
