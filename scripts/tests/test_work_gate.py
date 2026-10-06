"""Tests for the agent preflight and board report (work management specification sections 8, 17 and 18)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from work_gate import (  # noqa: E402
    Item, Sprint, item_from_api, preflight, report, sprint_release_problem, sprint_releases, sprint_state,
    status_problem,
)

SPRINT_1 = Sprint("Sprint 1", date(2026, 10, 2), 14)
# 2026-10-02 00:00 in Brussels (CEST, UTC+2) is 2026-10-01 22:00 UTC; the end, 2026-10-16 00:00, is 2026-10-15 22:00.
DURING = datetime(2026, 10, 5, 9, 0, tzinfo=timezone.utc)
CONTRACT = {
    "task": ("### Parent\n#323\n### Purpose\nWhy.\n### Bounded deliverable\nThe script.\n### Execution scope\nIt.\n"
             "### Delivery Stage\nDevelopment\n### Completion conditions\nIt works.\n### Dependencies\nNone.\n"
             "### Verification method\nTests.\n"),
    "improvement": ("### Parent\n#156\n### Purpose\nWhy.\n### Current situation\nNow.\n"
                    "### Desired enhancement\nBetter.\n"
                    "### Scope\nAll.\n### Acceptance criteria\nDone.\n### Dependencies\nNone.\n"
                    "### Verification method\nCheck.\n"),
}


def item(number: int, kind: str, **values: object) -> Item:
    defaults: dict[str, object] = {"title": f"Item {number}", "state": "open", "reason": None,
                                   "labels": frozenset({f"type:{kind}"}), "body": CONTRACT.get(kind, "")}
    defaults.update(values)
    return Item(number, **defaults)  # type: ignore[arg-type]


class SprintTests(unittest.TestCase):
    def test_boundaries_are_brussels_midnight_with_an_exclusive_end(self) -> None:
        self.assertTrue(SPRINT_1.active(datetime(2026, 10, 1, 22, 0, tzinfo=timezone.utc)))
        self.assertFalse(SPRINT_1.active(datetime(2026, 10, 1, 21, 59, tzinfo=timezone.utc)))
        self.assertTrue(SPRINT_1.active(datetime(2026, 10, 15, 21, 59, tzinfo=timezone.utc)))
        self.assertFalse(SPRINT_1.active(datetime(2026, 10, 15, 22, 0, tzinfo=timezone.utc)))

    def test_the_state_comes_from_the_sprint_record(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "docs/planning/sprints").mkdir(parents=True)
            (root / "docs/planning/sprints/sprint-01.md").write_text("| State | Canceled |\n", encoding="utf-8")
            self.assertEqual(sprint_state(SPRINT_1, root), "Canceled")
            self.assertIsNone(sprint_state(Sprint("Sprint 2", date(2026, 10, 16), 14), root))


class PreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        (self.root / "docs/planning/sprints").mkdir(parents=True)
        (self.root / "docs/planning/sprints/sprint-01.md").write_text("| State | Active |\n", encoding="utf-8")
        (self.root / "docs/planning/releases").mkdir(parents=True)
        (self.root / "docs/planning/releases/v1.0.md").write_text(
            "## Sprint sequence\n\n| Sprint | Dates |\n| --- | --- |\n| Sprint 1 | 2026-10-02 |\n", encoding="utf-8")
        self.parent = item(323, "improvement", milestone="v1.0", sprint=SPRINT_1)
        self.task = item(328, "task", milestone="v1.0", sprint=SPRINT_1, parent=323, assignees=("owner",),
                         stage="Development", prerequisites=[(324, "closed", "completed")])

    def failed(self, now: datetime = DURING) -> list[str]:
        items = {323: self.parent, 328: self.task}
        return [finding.rule for finding in preflight(self.task, items, now, self.root) if not finding.passed]

    def test_an_eligible_task_passes_every_condition(self) -> None:
        self.assertEqual(self.failed(), [])

    def test_a_contract_gap_or_unknown_fails_condition_one(self) -> None:
        self.task.body = self.task.body.replace("### Execution scope\nIt.\n", "")
        self.assertEqual(self.failed(), ["1. Hierarchy and contract"])
        self.task.body = CONTRACT["task"].replace("Tests.", "Unknown: needs clarification")
        self.assertEqual(self.failed(), ["1. Hierarchy and contract"])

    def test_outside_the_sprint_or_in_a_canceled_one_fails_condition_two(self) -> None:
        self.assertEqual(self.failed(datetime(2026, 10, 16, 8, 0, tzinfo=timezone.utc)), ["2. Active sprint"])
        (self.root / "docs/planning/sprints/sprint-01.md").write_text("| State | Canceled |\n", encoding="utf-8")
        self.assertEqual(self.failed(), ["2. Active sprint"])

    def test_a_task_without_a_sprint_fails_conditions_two_and_three(self) -> None:
        self.task.sprint = None
        self.assertEqual(self.failed(), ["2. Active sprint", "3. Matching sprint"])

    def test_mismatched_release_fails_condition_four(self) -> None:
        self.task.milestone = None
        self.assertEqual(self.failed(), ["4. Matching release"])

    def test_missing_stage_or_assignee_fails_condition_five(self) -> None:
        self.task.stage = None
        self.task.assignees = ()
        findings = preflight(self.task, {323: self.parent, 328: self.task}, DURING, self.root)
        self.assertEqual(findings[4].detail.split(".")[0], "Missing: assignee, Delivery Stage")

    def test_an_unfinished_or_canceled_prerequisite_fails_condition_six(self) -> None:
        self.task.prerequisites = [(327, "open", None), (326, "closed", "not_planned")]
        findings = preflight(self.task, {323: self.parent, 328: self.task}, DURING, self.root)
        self.assertIn("Not completed yet: #327, #326.", findings[5].detail)

    def test_a_closed_task_or_parent_fails_condition_seven(self) -> None:
        self.parent.state, self.parent.reason = "closed", "completed"
        self.assertEqual(self.failed(), ["7. Open and not canceled"])

    def test_an_outcome_item_is_not_executed_directly(self) -> None:
        findings = preflight(self.parent, {323: self.parent}, DURING, self.root)
        self.assertIn("is not a task", findings[0].detail)


class ReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.gettempdir())

    def test_status_must_match_the_closure_reason(self) -> None:
        self.assertIsNone(status_problem(item(1, "task", state="closed", reason="completed", status="Done")))
        self.assertIn("not Done", status_problem(item(1, "task", state="closed", reason="completed",
                                                      status="In Review")) or "")
        self.assertIn("not Canceled", status_problem(item(2, "task", state="closed", reason="not_planned",
                                                          status="Done")) or "")
        self.assertIn("is open but its Status is Done", status_problem(item(3, "story", status="Done")) or "")

    def test_findings_are_grouped_by_category(self) -> None:
        items = {
            13: item(13, "story", status="In Progress"),
            30: item(30, "story", status="Ready", sprint=SPRINT_1, prerequisites=[(31, "open", None)]),
            31: item(31, "story", status="Backlog"),
            40: item(40, "improvement", status="Blocked", sprint=SPRINT_1),
            41: item(41, "task", status="Ready", sprint=Sprint("Sprint 2", date(2026, 10, 16), 14), parent=40),
        }
        found = report(items, [(99, "Closes #41\n\n## What changed")], DURING, {})
        self.assertEqual([number for number, _ in found["Scheduling violations"]], [13, 41, 41])
        self.assertEqual([number for number, _ in found["Unestimated selected stories"]], [30])
        self.assertEqual([number for number, _ in found["Ready or selected items with contract gaps"]], [30])
        self.assertEqual([number for number, _ in found["Unavailable prerequisites"]], [30])
        self.assertEqual([number for number, _ in found["Blocked items without a recorded reason"]], [40])
        self.assertEqual([number for number, _ in found["Open items with contract gaps (allowed in Backlog)"]],
                         [13, 31])

    def test_a_prerequisite_in_the_same_sprint_is_available(self) -> None:
        items = {30: item(30, "story", sprint=SPRINT_1, points=3, prerequisites=[(31, "open", None)]),
                 31: item(31, "story", sprint=SPRINT_1, points=2)}
        self.assertEqual(report(items, [], DURING, {})["Unavailable prerequisites"], [])


class SprintReleaseTests(unittest.TestCase):
    RECORD = ("# Release v0.3\n\n## Sprint sequence\n\n| Sprint | Dates | Purpose |\n| --- | --- | --- |\n"
              "| Sprint 5 | 2026-10-03 | Delivery |\n| Sprint 8 | 2026-11-14 | Stabilization |\n\n"
              "## Scope decisions\n\n"
              "| Sprint 9 | not a sequence row |\n")
    HISTORY = ("# Release v0.1\n\n## Sprint sequence\n\n| Sprint | Date |\n| --- | --- |\n"
               "| [Sprint 1](../sprints/sprint-01.md) | 2026-09-29 |\n")

    def releases(self) -> dict[str, str]:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "docs/planning/releases").mkdir(parents=True)
            (root / "docs/planning/releases/v0.3.md").write_text(self.RECORD, encoding="utf-8")
            (root / "docs/planning/releases/v0.1.md").write_text(self.HISTORY, encoding="utf-8")
            return sprint_releases(root)

    def test_each_sprint_maps_to_the_release_whose_sequence_lists_it(self) -> None:
        self.assertEqual(self.releases(), {"Sprint 1": "v0.1", "Sprint 5": "v0.3", "Sprint 8": "v0.3"})

    def test_an_item_on_another_release_than_its_sprint_is_reported(self) -> None:
        releases = self.releases()
        sprint5 = Sprint("Sprint 5", date(2026, 10, 3), 14)
        self.assertIsNone(sprint_release_problem(item(13, "story", milestone="v0.3", sprint=sprint5), releases))
        self.assertIn("belongs to v0.3", sprint_release_problem(item(92, "task", milestone="v0.1", sprint=sprint5),
                                                                releases) or "")
        self.assertIn("belongs to no release record",
                      sprint_release_problem(item(1, "task", sprint=Sprint("Sprint 20", date(2027, 6, 1), 14)),
                                             releases) or "")
        self.assertIsNone(sprint_release_problem(item(2, "task"), releases))

    def test_the_report_lists_mismatches_as_violations(self) -> None:
        sprint5 = Sprint("Sprint 5", date(2026, 10, 3), 14)
        found = report({92: item(92, "task", state="closed", reason="completed", status="Done", milestone="v0.1",
                                 sprint=sprint5)}, [], DURING, {"Sprint 5": "v0.3"})
        self.assertEqual([number for number, _ in found["Sprint and release mismatches"]], [92])


class ApiTests(unittest.TestCase):
    def test_a_project_item_is_read_with_its_fields(self) -> None:
        node = {
            "status": {"name": "Ready"}, "stage": {"name": "Testing"}, "points": {"number": 5},
            "sprint": {"title": "Sprint 1", "startDate": "2026-10-02", "duration": 14},
            "content": {"number": 30, "title": "Story", "state": "OPEN", "stateReason": None, "body": "",
                        "milestone": {"title": "v1.0"}, "labels": {"nodes": [{"name": "type:story"}]},
                        "assignees": {"nodes": [{"login": "owner"}]}, "parent": {"number": 131},
                        "blockedBy": {"nodes": [{"number": 31, "state": "CLOSED", "stateReason": "COMPLETED"}]}},
        }
        found = item_from_api(node)
        assert found is not None
        self.assertEqual((found.status, found.stage, found.points, found.sprint, found.parent, found.prerequisites),
                         ("Ready", "Testing", 5, SPRINT_1, 131, [(31, "closed", "completed")]))
        self.assertIsNone(item_from_api({"content": {}}))


if __name__ == "__main__":
    unittest.main()
