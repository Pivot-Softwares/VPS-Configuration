"""Tests for the board bridge (specification section 22, A11)."""

from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from board_bridge import (  # noqa: E402
    ITERATION_CONFIGURATION_INPUT, OPTION_INPUT, Board, BridgeError, Field, parse_changes, run, sync_issue_types)

CONFIG = {"organization": {"projectV2": {
    "id": "PVT_1", "title": "VPS Configuration", "url": "https://github.com/orgs/Pivot-Softwares/projects/1",
    "fields": {"nodes": [
        {"id": "F_TITLE", "name": "Title", "dataType": "TITLE"},
        {"id": "F_STATUS", "name": "Status", "dataType": "SINGLE_SELECT",
         "options": [{"id": "o_backlog", "name": "Backlog"}, {"id": "o_ready", "name": "Ready"},
                     {"id": "o_done", "name": "Done"}, {"id": "o_canceled", "name": "Canceled"}]},
        {"id": "F_SPRINT", "name": "Sprint", "dataType": "ITERATION",
         "configuration": {"duration": 14, "startDay": 1,
                           "iterations": [{"id": "i_1", "title": "Sprint 1", "startDate": "2026-10-06", "duration": 14}],
                           "completedIterations": []}},
        {"id": "F_AREA", "name": "Area", "dataType": "SINGLE_SELECT",
         "options": [{"id": "o_platform", "name": "Platform", "color": "RED", "description": "Old area"},
                     {"id": "o_tooling", "name": "Tooling", "color": "BLUE", "description": ""}]},
        {"id": "F_POINTS", "name": "Story Points", "dataType": "NUMBER"},
        {"id": "F_START", "name": "Start date", "dataType": "DATE"},
        {},
    ]},
    "views": {"nodes": [{"id": "V_1", "number": 1, "name": "Product backlog", "layout": "TABLE_LAYOUT",
                         "filter": "is:open"}]},
    "workflows": {"nodes": [{"number": 1, "name": "Auto-close issue", "enabled": True},
                            {"number": 2, "name": "Auto-add to project", "enabled": False}]},
}}}
ITEMS = {"node": {"items": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": [
    {"id": "PVTI_12", "type": "ISSUE", "content": {"__typename": "Issue", "number": 12}, "fieldValues": {"nodes": [
        {"name": "Backlog", "field": {"name": "Status"}},
        {"name": "Platform", "field": {"name": "Area"}},
        {"title": "Sprint 1", "field": {"name": "Sprint"}},
        {"number": 3.0, "field": {"name": "Story Points"}},
        {"text": "Task: one", "field": {"name": "Title"}},
        {},
    ]}},
    {"id": "PVTI_DRAFT", "type": "DRAFT_ISSUE", "content": {"__typename": "DraftIssue"},
     "fieldValues": {"nodes": []}},
]}}}


ISSUE_PATH = re.compile(r"repos/Pivot-Softwares/VPS-Configuration/issues/(\d+)")


def wrapped(name: str) -> dict:
    return {"kind": "NON_NULL", "name": None, "ofType": {"kind": "LIST", "name": None, "ofType": {
        "kind": "NON_NULL", "name": None, "ofType": {"kind": "INPUT_OBJECT", "name": name}}}}


class FakeGh:
    """Answers the bridge's gh calls from fixtures, applies field updates like GitHub, and records every call.

    ids_in_schema: whether GitHub's input types take option and iteration ids. keeps_values: whether items keep their
    values through a field update (False plays the RaidManager incident, where every value was lost).
    """

    def __init__(self, items: dict | None = None, errors: list | None = None, ids_in_schema: bool = True,
                 keeps_values: bool = True) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.bodies: list[dict] = []
        self.config: dict[str, Any] = copy.deepcopy(CONFIG)
        self.item_page: dict[str, Any] = copy.deepcopy(items or ITEMS)
        self.errors = errors
        self.ids_in_schema, self.keeps_values = ids_in_schema, keeps_values
        # Issue states by number, for the REST reads and writes of the bridge; issues are open unless listed.
        self.states: dict[int, str] = {}

    def __call__(self, *arguments: str) -> str:
        self.calls.append(arguments)
        issue = ISSUE_PATH.fullmatch(next((argument for argument in arguments if argument.startswith("repos/")), ""))
        if issue and "-X" not in arguments:
            number = int(issue.group(1))
            return json.dumps({"node_id": f"I_{number}", "state": self.states.get(number, "open")})
        if issue:
            return "{}"
        if "--input" in arguments:
            with open(arguments[arguments.index("--input") + 1], encoding="utf-8") as handle:
                body = json.load(handle)
            self.bodies.append(body)
            self.update_field(body["variables"]["input"])
            return json.dumps({"data": {"updateProjectV2Field": {"projectV2Field": {"id": "F", "name": "F"}}}})
        query = next(argument for argument in arguments if argument.startswith("query="))
        if "__type(name" in query:
            return json.dumps({"data": {"__type": self.input_type(next(
                argument[5:] for argument in arguments if argument.startswith("name=")))}})
        if "organization(login" in query:
            return json.dumps({"data": self.config})
        if "items(first" in query:
            return json.dumps({"data": self.item_page, **({"errors": self.errors} if self.errors else {})})
        if "addProjectV2ItemById" in query:
            return json.dumps({"data": {"addProjectV2ItemById": {"item": {"id": "PVTI_13"}}}})
        return json.dumps({"data": {}})

    def input_type(self, name: str) -> dict:
        ident = [{"name": "id", "type": {"kind": "SCALAR", "name": "String"}}] if self.ids_in_schema else []
        scalars = {OPTION_INPUT: ["name", "color", "description"], "ProjectV2Iteration": ["title", "startDate",
                                                                                         "duration"]}
        if name == ITERATION_CONFIGURATION_INPUT:
            return {"inputFields": [{"name": "iterations", "type": wrapped("ProjectV2Iteration")},
                                    {"name": "startDate", "type": {"kind": "SCALAR", "name": "Date"}},
                                    {"name": "duration", "type": {"kind": "SCALAR", "name": "Int"}}]}
        return {"inputFields": ident + [{"name": field, "type": {"kind": "SCALAR", "name": "String"}}
                                        for field in scalars[name]]}

    def update_field(self, update: dict) -> None:
        node = next(node for node in self.config["organization"]["projectV2"]["fields"]["nodes"]
                    if node.get("id") == update["fieldId"])
        if "singleSelectOptions" in update:
            old = {option["id"]: option["name"] for option in node["options"]}
            node["options"] = [{**option, "id": option.get("id") or f"o_new_{option['name']}"}
                               for option in update["singleSelectOptions"]]
            names = {option["id"]: option["name"] for option in node["options"]}
            renamed = {name: names[ident] for ident, name in old.items() if ident in names}
        else:
            configuration = update["iterationConfiguration"]
            old = {i["id"]: i["title"] for i in node["configuration"]["iterations"]}
            node["configuration"]["iterations"] = [{**i, "id": i.get("id") or f"i_new_{i['title']}"}
                                                   for i in configuration["iterations"]]
            titles = {i["id"]: i["title"] for i in node["configuration"]["iterations"]}
            renamed = {title: titles[ident] for ident, title in old.items() if ident in titles}
        for item in self.item_page["node"]["items"]["nodes"]:
            values = item["fieldValues"]["nodes"]
            for value in list(values):
                if (value.get("field") or {}).get("name") != node["name"]:
                    continue
                key = "name" if "name" in value else "title"
                if not self.keeps_values or value[key] not in renamed:
                    values.remove(value)
                else:
                    value[key] = renamed[value[key]]

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
        self.assertEqual(items[12]["fields"], {"Status": "Backlog", "Area": "Platform", "Sprint": "Sprint 1",
                                               "Story Points": 3.0, "Title": "Task: one"})

    def test_hidden_items_stop_the_read_instead_of_disappearing(self) -> None:
        issue_12 = {"id": "PVTI_12", "type": "ISSUE", "content": {"number": 12}, "fieldValues": {"nodes": []}}
        hidden = {"node": {"items": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": [
            issue_12,
            {"id": "PVTI_5", "type": "REDACTED", "content": None, "fieldValues": {"nodes": []}},
            {"id": "PVTI_7", "type": "ISSUE", "content": {}, "fieldValues": {"nodes": []}},
        ]}}}
        with self.assertRaises(BridgeError) as raised:
            board(FakeGh(items=hidden)).items()
        message = str(raised.exception)
        self.assertIn("2 of 3 Project items are hidden", message)
        self.assertIn("Pivot-Softwares/VPS-Configuration", message)

    def test_graphql_errors_are_reported(self) -> None:
        with self.assertRaises(BridgeError) as raised:
            board(FakeGh(errors=[{"message": "Resource not accessible by integration"}])).items()
        self.assertIn("Resource not accessible by integration", str(raised.exception))

    def test_read_items_reports_the_item_types(self) -> None:
        result, _ = run("read-items", {}, lambda: board(FakeGh()))
        self.assertEqual(result["item_types"], {"ISSUE": 1, "DRAFT_ISSUE": 1})

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
        self.assertEqual(items["items"], {})


def iteration_field(current: list[tuple[str, str]], completed: list[tuple[str, str]]) -> Field:
    def iterations(pairs: list[tuple[str, str]]) -> list[dict]:
        return [{"id": ident, "title": title, "startDate": "2026-01-01", "duration": 14} for ident, title in pairs]
    field = Field.from_api({"id": "F", "name": "Sprint", "dataType": "ITERATION", "configuration": {
        "duration": 14, "iterations": iterations(current), "completedIterations": iterations(completed)}})
    assert field is not None
    return field


class IterationLookupTests(unittest.TestCase):
    def test_a_current_or_future_iteration_wins_over_a_completed_one(self) -> None:
        field = iteration_field([("i_new", "Sprint 1")], [("i_old", "Sprint 1")])
        self.assertEqual(field.resolve("Sprint 1"), "i_new")

    def test_a_title_only_completed_once_still_resolves(self) -> None:
        self.assertEqual(iteration_field([], [("i_old", "Sprint 0")]).resolve("Sprint 0"), "i_old")

    def test_ambiguous_titles_are_refused(self) -> None:
        for current, completed in (([("a", "Sprint 1"), ("b", "Sprint 1")], []),
                                   ([], [("a", "Sprint 1"), ("b", "Sprint 1")])):
            with self.subTest(current=current, completed=completed), self.assertRaises(BridgeError) as raised:
                iteration_field(current, completed).resolve("Sprint 1")
            self.assertIn("more than one iteration", str(raised.exception))

    def test_a_current_title_is_not_ambiguous_because_of_completed_duplicates(self) -> None:
        field = iteration_field([("i_new", "Sprint 1")], [("a", "Sprint 1"), ("b", "Sprint 1")])
        self.assertEqual(field.resolve("Sprint 1"), "i_new")


SPRINT_3 = {"field": "Sprint", "title": "Sprint 3", "start_date": "2026-11-03"}


class AddIterationTests(unittest.TestCase):
    def test_dry_run_is_the_default_and_writes_nothing(self) -> None:
        gh = FakeGh()
        result = board(gh).add_iteration(SPRINT_3)
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["add"], {"title": "Sprint 3", "startDate": "2026-11-03", "duration": 14})
        self.assertEqual(result["keep"][0]["id"], "i_1")
        self.assertEqual(gh.bodies, [])

    def test_invalid_iterations_are_refused(self) -> None:
        payloads: tuple[dict, ...] = (
            {**SPRINT_3, "title": "Sprint 1"}, {**SPRINT_3, "start_date": "2026-10-13"},
            {**SPRINT_3, "start_date": "soon"}, {**SPRINT_3, "duration": 0}, {**SPRINT_3, "duration": True},
            {**SPRINT_3, "field": "Status"}, {**SPRINT_3, "field": "Owner"}, {**SPRINT_3, "title": " "},
            {**SPRINT_3, "extra": 1}, {"field": "Sprint", "title": "Sprint 3"}, {**SPRINT_3, "dry_run": "no"})
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(BridgeError):
                board(FakeGh()).add_iteration(payload)

    def test_apply_sends_every_iteration_with_its_id_and_keeps_values(self) -> None:
        gh = FakeGh()
        result = board(gh).add_iteration({**SPRINT_3, "dry_run": False})
        (body,) = gh.bodies
        configuration = body["variables"]["input"]["iterationConfiguration"]
        self.assertEqual([i.get("id") for i in configuration["iterations"]], ["i_1", None])
        self.assertEqual(configuration["startDate"], "2026-10-06")
        self.assertNotIn("Sprint 3", body["query"])
        self.assertTrue(result["ids_sent"])
        self.assertEqual((result["restored"], result["cleared"]), ([], []))
        self.assertEqual(gh.mutations(), [])
        self.assertIn("Sprint 3", [i["title"] for i in result["iterations"]])

    def test_values_dropped_by_github_are_set_again(self) -> None:
        gh = FakeGh(ids_in_schema=False, keeps_values=False)
        result = board(gh).add_iteration({**SPRINT_3, "dry_run": False})
        self.assertFalse(result["ids_sent"])
        self.assertEqual(result["restored"], [{"issue": 12, "value": "Sprint 1"}])
        (update,) = gh.mutations()
        self.assertIn("value=i_new_Sprint 1", update)


AREAS = [{"name": "Security", "from": "Platform", "color": "RED"}, {"name": "Process", "description": "Work"}]


class SetOptionsTests(unittest.TestCase):
    def test_dry_run_shows_kept_renamed_new_and_removed_options(self) -> None:
        gh = FakeGh()
        result = board(gh).set_options({"field": "Area", "options": AREAS})
        self.assertEqual([(o["id"], o["name"]) for o in result["options"]],
                         [("o_platform", "Security"), (None, "Process")])
        self.assertEqual(result["options"][0]["description"], "Old area")
        self.assertEqual(result["options"][1]["color"], "GRAY")
        self.assertEqual((result["renamed"], result["removed"], result["removed_in_use"]),
                         ({"Platform": "Security"}, ["Tooling"], {}))
        self.assertEqual(gh.bodies, [])

    def test_apply_sends_existing_ids_and_keeps_values(self) -> None:
        gh = FakeGh()
        result = board(gh).set_options({"field": "Area", "options": AREAS, "dry_run": False})
        (body,) = gh.bodies
        sent = body["variables"]["input"]["singleSelectOptions"]
        self.assertEqual(sent[0], {"id": "o_platform", "name": "Security", "color": "RED", "description": "Old area"})
        self.assertNotIn("id", sent[1])
        self.assertEqual((result["restored"], result["cleared"]), ([], []))
        self.assertEqual([o["name"] for o in result["options_after"]], ["Security", "Process"])

    def test_values_dropped_by_github_are_set_again_under_the_new_name(self) -> None:
        gh = FakeGh(keeps_values=False)
        result = board(gh).set_options({"field": "Area", "options": AREAS, "dry_run": False})
        self.assertEqual(result["restored"], [{"issue": 12, "value": "Security"}])
        (update,) = gh.mutations()
        self.assertIn("value=o_platform", update)

    def test_options_in_use_are_removed_only_when_allowed(self) -> None:
        replace = [{"name": "Security"}]
        dry_run = board(FakeGh()).set_options({"field": "Area", "options": replace})
        self.assertEqual(dry_run["removed_in_use"], {"Platform": [12]})
        refused = FakeGh()
        with self.assertRaises(BridgeError) as raised:
            board(refused).set_options({"field": "Area", "options": replace, "dry_run": False})
        self.assertIn("{'Platform': [12]}", str(raised.exception))
        self.assertEqual(refused.bodies, [])
        gh = FakeGh()
        result = board(gh).set_options({"field": "Area", "options": replace, "remove_used": True, "dry_run": False})
        self.assertEqual(result["removed_in_use"], {"Platform": [12]})
        self.assertEqual(gh.mutations(), [])

    def test_without_ids_in_the_schema_nothing_is_changed(self) -> None:
        gh = FakeGh(ids_in_schema=False)
        with self.assertRaises(BridgeError) as raised:
            board(gh).set_options({"field": "Area", "options": AREAS, "dry_run": False})
        self.assertIn("nothing was changed", str(raised.exception))
        self.assertEqual(gh.bodies, [])

    def test_invalid_options_are_refused(self) -> None:
        payloads: tuple[dict, ...] = (
            {"field": "Area", "options": []}, {"field": "Area", "options": [{"name": "A", "color": "TEAL"}]},
            {"field": "Area", "options": [{"name": "A"}, {"name": "A"}]},
            {"field": "Area", "options": [{"name": "A", "from": "Nope"}]},
            {"field": "Area", "options": [{"name": "A", "from": "Tooling"}, {"name": "B", "from": "Tooling"}]},
            {"field": "Area", "options": [{"name": "A", "owner": "x"}]}, {"field": "Area", "options": ["A"]},
            {"field": "Sprint", "options": [{"name": "A"}]}, {"field": "Area", "options": [{"name": "A"}],
                                                              "remove_used": "yes"})
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(BridgeError):
                board(FakeGh()).set_options(payload)

    def test_the_operations_are_reachable_through_run(self) -> None:
        result, passed = run("set-options", {"field": "Area", "options": AREAS}, lambda: board(FakeGh()))
        self.assertTrue(passed and result["dry_run"])
        result, _ = run("add-iteration", SPRINT_3, lambda: board(FakeGh()))
        self.assertEqual(result["add"]["title"], "Sprint 3")


ORG_TYPES = [{"name": "Task", "is_enabled": True}, {"name": "Bug", "is_enabled": True},
             {"name": "Feature", "is_enabled": False}]
REPO_ISSUES = [[
    {"number": 3, "labels": [{"name": "type:epic"}], "type": None},
    {"number": 8, "labels": [{"name": "type:task"}], "type": {"name": "Task"}},
    {"number": 21, "labels": [{"name": "type:bug"}, {"name": "needs-parent"}], "type": {"name": "Task"}},
    {"number": 26, "labels": [], "pull_request": {}},
], [
    {"number": 30, "labels": [], "type": None},
    {"number": 31, "labels": [{"name": "type:story"}, {"name": "type:task"}], "type": None},
]]


class TypesGh(FakeGh):
    """Adds the issue types and issues REST answers to the fake."""

    def __call__(self, *arguments: str) -> str:
        if "orgs/Pivot-Softwares/issue-types" in arguments and "-X" not in arguments:
            self.calls.append(arguments)
            return json.dumps(ORG_TYPES)
        if any(argument.startswith("repos/Pivot-Softwares/VPS-Configuration/issues?") for argument in arguments):
            self.calls.append(arguments)
            return json.dumps(REPO_ISSUES)
        if "-X" in arguments:
            self.calls.append(arguments)
            return "{}"
        return super().__call__(*arguments)

    def writes(self) -> list[tuple[str, ...]]:
        return [call for call in self.calls if "-X" in call]


class SyncIssueTypesTests(unittest.TestCase):
    def test_dry_run_lists_the_types_to_create_and_the_issues_to_set(self) -> None:
        gh = TypesGh()
        result = sync_issue_types(board(gh), {})
        self.assertEqual(result["types_to_create"], ["Epic", "Story", "Improvement", "Spike"])
        self.assertEqual(result["types_disabled"], ["Feature"])
        self.assertEqual(result["changes"], [{"issue": 3, "from": None, "to": "Epic", "result": "would set"},
                                             {"issue": 21, "from": "Task", "to": "Bug", "result": "would set"}])
        self.assertEqual(result["skipped"], [{"issue": 30, "type_labels": []},
                                             {"issue": 31, "type_labels": ["type:story", "type:task"]}])
        self.assertEqual(gh.writes(), [])

    def test_apply_creates_only_missing_types_then_sets_the_types(self) -> None:
        gh = TypesGh()
        result = sync_issue_types(board(gh), {"dry_run": False})
        self.assertEqual(result["types_created"], ["Epic", "Story", "Improvement", "Spike"])
        creates = [call for call in gh.writes() if "POST" in call]
        self.assertEqual([call[call.index("-f") + 1] for call in creates],
                         ["name=Epic", "name=Story", "name=Improvement", "name=Spike"])
        self.assertTrue(all("is_enabled=true" in call for call in creates))
        patches = [call for call in gh.writes() if "PATCH" in call]
        self.assertEqual([(call[3], call[-1]) for call in patches],
                         [("repos/Pivot-Softwares/VPS-Configuration/issues/3", "type=Epic"),
                          ("repos/Pivot-Softwares/VPS-Configuration/issues/21", "type=Bug")])

    def test_unknown_payload_keys_are_refused(self) -> None:
        for payload in ({"issues": [3]}, {"dry_run": "no"}):
            with self.subTest(payload=payload), self.assertRaises(BridgeError):
                sync_issue_types(board(TypesGh()), payload)

    def test_the_operation_is_reachable_through_run(self) -> None:
        result, passed = run("sync-issue-types", {}, lambda: board(TypesGh()))
        self.assertTrue(passed and result["dry_run"])


class IssueStateTests(unittest.TestCase):
    def patches(self, gh: FakeGh) -> list[tuple[str, ...]]:
        return [call for call in gh.calls if "PATCH" in call]

    def test_done_closes_as_completed_and_canceled_as_not_planned(self) -> None:
        gh = FakeGh()
        result = board(gh).set_fields({"dry_run": False, "changes": [
            {"issue": 12, "field": "Status", "value": "Done"}, {"issue": 13, "field": "Status", "value": "Canceled"}]})
        self.assertEqual([(entry["issue"], entry["action"], entry["reason"], entry["result"])
                          for entry in result["issues"]],
                         [(12, "close", "completed", "closed"), (13, "close", "not_planned", "closed")])
        self.assertEqual([call[-4:] for call in self.patches(gh)],
                         [("-f", "state=closed", "-f", "state_reason=completed"),
                          ("-f", "state=closed", "-f", "state_reason=not_planned")])

    def test_another_status_reopens_a_closed_issue_and_a_closed_done_issue_is_left(self) -> None:
        gh = FakeGh()
        gh.states = {12: "closed", 13: "closed"}
        result = board(gh).set_fields({"dry_run": False, "changes": [
            {"issue": 12, "field": "Status", "value": "Ready"}, {"issue": 13, "field": "Status", "value": "Done"}]})
        self.assertEqual(result["issues"], [{"issue": 12, "status": "Ready", "action": "reopen", "result": "reopened"}])
        self.assertEqual([call[-2:] for call in self.patches(gh)], [("-f", "state=open")])

    def test_a_status_already_set_still_closes_an_open_issue(self) -> None:
        gh = FakeGh()
        gh.item_page["node"]["items"]["nodes"][0]["fieldValues"]["nodes"][0]["name"] = "Done"
        result = board(gh).set_fields({"dry_run": False,
                                       "changes": [{"issue": 12, "field": "Status", "value": "Done"}]})
        self.assertEqual(result["changes"][0]["result"], "skipped")
        self.assertEqual(result["issues"][0]["result"], "closed")

    def test_dry_run_and_other_fields_change_no_issue(self) -> None:
        gh = FakeGh()
        result = board(gh).set_fields({"changes": [{"issue": 12, "field": "Status", "value": "Done"},
                                                   {"issue": 13, "field": "Story Points", "value": 2}]})
        self.assertEqual(result["issues"], [{"issue": 12, "status": "Done", "action": "close", "reason": "completed",
                                             "result": "would close"}])
        self.assertEqual(self.patches(gh), [])


class AddItemsTests(unittest.TestCase):
    def test_a_new_issue_is_added_with_the_first_status(self) -> None:
        gh = FakeGh()
        result = board(gh).add_items({"dry_run": False, "issues": [13, 12]})
        self.assertEqual(result["items"], [{"issue": 12, "actions": [], "result": "skipped"},
                                           {"issue": 13, "actions": ["add", "Status Backlog"], "result": "applied"}])
        (update,) = gh.mutations()
        self.assertIn("item=PVTI_13", update)
        self.assertIn("value=o_backlog", update)

    def test_an_item_without_a_status_gets_one_and_a_dry_run_writes_nothing(self) -> None:
        gh = FakeGh()
        gh.item_page["node"]["items"]["nodes"][0]["fieldValues"]["nodes"].pop(0)
        result = board(gh).add_items({"issues": [12]})
        self.assertEqual(result["items"], [{"issue": 12, "actions": ["Status Backlog"], "result": "would apply"}])
        self.assertEqual(gh.mutations(), [])

    def test_invalid_payloads_are_refused(self) -> None:
        payloads: tuple[dict, ...] = ({}, {"issues": []}, {"issues": [0]}, {"issues": ["12"]},
                                      {"issues": [12], "extra": 1}, {"issues": list(range(1, 52))})
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(BridgeError):
                board(FakeGh()).add_items(payload)

    def test_dump_config_lists_the_project_workflows(self) -> None:
        config, _ = run("dump-config", {}, lambda: board(FakeGh()))
        self.assertEqual([(flow["name"], flow["enabled"]) for flow in config["workflows"]],
                         [("Auto-close issue", True), ("Auto-add to project", False)])
        result, _ = run("add-items", {"issues": [13]}, lambda: board(FakeGh()))
        self.assertTrue(result["dry_run"])


if __name__ == "__main__":
    unittest.main()
