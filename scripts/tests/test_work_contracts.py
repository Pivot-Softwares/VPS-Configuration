"""Tests for the work management rules shared by the hierarchy guard and the agent preflight."""

from __future__ import annotations

import sys
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from work_contracts import (  # noqa: E402
    ADOPTED, BY_TYPE, TASK, canceled_prerequisites, contract_problem, dependency_cycles, missing_sections,
    release_record_problem, scope_milestone_problem, sections, task_milestone_problem, unknown_sections,
)

TASK_BODY = """### Parent
#323

### Purpose
Make the guard enforce the contract.

### Bounded deliverable
The contract check.

### Execution scope
`scripts/work_contracts.py` and its tests.

### Delivery Stage
Development

### Dependencies
#324

### Completion conditions
The check flags a missing section.

### Verification method
Unit tests.
"""


class SectionTests(unittest.TestCase):
    def test_headings_of_level_two_and_three_are_read(self) -> None:
        found = sections("## Parent\n#13\n\n### Delivery Stage\nTesting\n")
        self.assertEqual(found, {"parent": "#13", "delivery stage": "Testing"})

    def test_a_complete_task_passes(self) -> None:
        self.assertEqual(missing_sections(TASK, TASK_BODY), [])

    def test_missing_and_empty_sections_are_listed(self) -> None:
        body = TASK_BODY.replace("### Dependencies\n#324", "### Dependencies\n_No response_")
        body = body.replace("### Delivery Stage\nDevelopment\n", "")
        self.assertEqual(missing_sections(TASK, body), ["Dependencies", "Delivery Stage"])

    def test_an_alternative_heading_satisfies_a_common_requirement(self) -> None:
        body = TASK_BODY.replace("### Completion conditions", "### Acceptance criteria")
        self.assertEqual(missing_sections(TASK, body), [])

    def test_unknown_answers_count_as_present_but_block_readiness(self) -> None:
        body = TASK_BODY.replace("Unit tests.", "Unknown: needs clarification")
        self.assertEqual(missing_sections(TASK, body), [])
        self.assertEqual(unknown_sections(TASK, body), ["Verification", "Verification method"])

    def test_a_quoted_marker_is_not_an_unknown_answer(self) -> None:
        body = TASK_BODY.replace("Unit tests.", 'Gaps are recorded as "Unknown: needs clarification".')
        self.assertEqual(unknown_sections(TASK, body), [])
        body = TASK_BODY.replace("Unit tests.", "- Unknown: needs clarification (owner)")
        self.assertEqual(unknown_sections(TASK, body), ["Verification", "Verification method"])

    def test_every_type_has_its_own_requirements(self) -> None:
        self.assertEqual(len(BY_TYPE), 7)
        self.assertIn("Parent", missing_sections("type:story", ""))
        self.assertNotIn("Parent", missing_sections("type:epic", ""))
        self.assertIn("Timebox", missing_sections("type:spike", ""))
        self.assertIn("Affected environment", missing_sections("type:bug", ""))


class IssueFormTests(unittest.TestCase):
    def test_every_issue_form_produces_a_complete_contract(self) -> None:
        forms = Path(__file__).resolve().parents[2] / ".github" / "ISSUE_TEMPLATE"
        for kind, name in (("epic", "1-epic"), ("feature", "2-feature"), ("story", "3-story"),
                           ("improvement", "4-improvement"), ("bug", "5-bug"), ("task", "6-task"),
                           ("spike", "7-spike")):
            text = (forms / f"{name}.yml").read_text(encoding="utf-8")
            labels = [line.split("label:", 1)[1].strip() for line in text.splitlines()
                      if line.strip().startswith("label:")]
            body = "".join(f"### {label}\n\nanswer\n\n" for label in labels)
            with self.subTest(form=name):
                self.assertIn(f'labels: ["type:{kind}"]', text)
                self.assertEqual(missing_sections(f"type:{kind}", body), [])


class ContractProblemTests(unittest.TestCase):
    def test_new_open_items_are_checked(self) -> None:
        problem = contract_problem(TASK, "open", ADOPTED + timedelta(minutes=1), "")
        self.assertIn("missing: Parent, Purpose", problem or "")
        self.assertIsNone(contract_problem(TASK, "open", ADOPTED + timedelta(minutes=1), TASK_BODY))

    def test_older_closed_and_untyped_items_are_exempt(self) -> None:
        self.assertIsNone(contract_problem(TASK, "open", ADOPTED - timedelta(minutes=1), ""))
        self.assertIsNone(contract_problem(TASK, "closed", ADOPTED + timedelta(minutes=1), ""))
        self.assertIsNone(contract_problem(None, "open", ADOPTED + timedelta(minutes=1), ""))


class MilestoneTests(unittest.TestCase):
    def test_task_shares_its_parents_milestone(self) -> None:
        self.assertIsNone(task_milestone_problem("v1.0", 323, "v1.0"))
        self.assertIn("parent #323's is none", task_milestone_problem("v1.0", 323, None) or "")

    def test_feature_milestone_requires_its_whole_scope(self) -> None:
        self.assertIsNone(scope_milestone_problem(None, [(1, "v1.0"), (2, "v1.1")]))
        self.assertIsNone(scope_milestone_problem("v1.0", [(1, "v1.0")]))
        self.assertIn("#2 is not in that release", scope_milestone_problem("v1.0", [(1, "v1.0"), (2, None)]) or "")


class DependencyTests(unittest.TestCase):
    def test_cycles_are_found_once(self) -> None:
        self.assertEqual(dependency_cycles({1: [2], 2: [3], 3: [1], 4: [1]}), [[1, 2, 3]])
        self.assertEqual(dependency_cycles({1: [2], 2: []}), [])
        self.assertEqual(dependency_cycles({5: [5]}), [[5]])

    def test_only_completed_prerequisites_are_satisfied(self) -> None:
        found = canceled_prerequisites([(1, "closed", "completed"), (2, "closed", "not_planned"), (3, "open", None),
                                        (4, "closed", None), (5, "closed", "duplicate")])
        self.assertEqual(found, [2, 5])


class ReleaseRecordTests(unittest.TestCase):
    def test_a_released_record_with_a_delivery_date_passes(self) -> None:
        record = "| State | Released |\n| Actual delivery date | 2027-01-15 |\n"
        self.assertIsNone(release_record_problem(record))

    def test_missing_or_unfinished_records_fail(self) -> None:
        self.assertEqual(release_record_problem(None), "its release record is missing")
        self.assertEqual(release_record_problem("| State | Stabilizing |"),
                         "its release record doesn't show the state Released")
        self.assertEqual(release_record_problem("| State | Released |\n| Actual delivery date | Unknown |"),
                         "its release record has no actual delivery date")


if __name__ == "__main__":
    unittest.main()
