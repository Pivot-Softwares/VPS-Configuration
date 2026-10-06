"""Tests for the hierarchy guard: the work management specification's rules it checks with GITHUB_TOKEN."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import project_hierarchy  # noqa: E402
from project_hierarchy import (  # noqa: E402
    DEPENDENCY_PROBLEM, NEEDS_CONTRACT, NEEDS_PARENT, Guard, Issue, Node, chain_problem, closing_numbers,
    completion_problem, parent_problem, placement_problem, prerequisite_problem,
)
from work_contracts import ADOPTED  # noqa: E402


def issue(number: int, kind: str, state: str = "open", reason: str | None = None, *extra: str) -> Issue:
    if reason is None and state == "closed":
        reason = "completed"
    return Issue(number, state, frozenset({f"type:{kind}", *extra}), reason)


class ParentRuleTests(unittest.TestCase):
    def test_epic_has_no_parent(self) -> None:
        self.assertIsNone(parent_problem(issue(7, "epic"), None))
        self.assertIn("An epic has no parent", parent_problem(issue(7, "epic"), issue(1, "epic")) or "")

    def test_each_level_needs_the_level_above(self) -> None:
        cases = [("feature", "epic"), ("story", "feature"), ("improvement", "feature"), ("bug", "feature"),
                 ("spike", "feature"), ("task", "story"), ("task", "improvement"), ("task", "bug"), ("task", "spike")]
        for kind, parent in cases:
            with self.subTest(kind=kind, parent=parent):
                self.assertIsNone(parent_problem(issue(2, kind), issue(1, parent)))

    def test_missing_parent_names_the_allowed_types(self) -> None:
        self.assertEqual(parent_problem(issue(100, "task"), None),
                         "Add this task as a sub-issue of a story, improvement, bug or spike.")
        self.assertEqual(parent_problem(issue(37, "spike"), None), "Add this spike as a sub-issue of a feature.")
        self.assertEqual(parent_problem(issue(13, "story"), None), "Add this story as a sub-issue of a feature.")

    def test_wrong_parent_level_fails(self) -> None:
        self.assertEqual(parent_problem(issue(13, "story"), issue(7, "epic")),
                         "Its parent #7 is an epic; a story belongs under a feature.")
        self.assertEqual(parent_problem(issue(57, "task"), issue(9, "feature")),
                         "Its parent #9 is a feature; a task belongs under a story, improvement, bug or spike.")
        self.assertEqual(parent_problem(issue(37, "spike"), issue(15, "story")),
                         "Its parent #15 is a story; a spike belongs under a feature.")

    def test_a_task_on_another_milestone_than_its_parent_fails(self) -> None:
        task = Issue(261, "closed", frozenset({"type:task"}), "completed", milestone="v1.0")
        improvement = Issue(260, "closed", frozenset({"type:improvement"}), "completed")
        self.assertEqual(parent_problem(task, improvement),
                         "This task's milestone is `v1.0` but its parent #260's is none; a task shares its parent's "
                         "release milestone (specification section 15).")

    def test_an_outcome_item_chooses_its_release_independently_of_its_feature(self) -> None:
        feature = Issue(259, "open", frozenset({"type:feature"}))
        self.assertIsNone(parent_problem(Issue(283, "open", frozenset({"type:improvement"}), milestone="v1.0"),
                                         feature))
        self.assertIsNone(parent_problem(Issue(284, "open", frozenset({"type:story"})),
                                         Issue(259, "open", frozenset({"type:feature"}), milestone="v1.0")))

    def test_a_feature_milestone_must_cover_its_whole_scope(self) -> None:
        feature = Issue(259, "open", frozenset({"type:feature"}), milestone="v1.0")
        node = Node(feature, issue(142, "epic"), [Issue(283, "open", frozenset({"type:improvement"}), milestone="v1.0"),
                                                 Issue(284, "open", frozenset({"type:story"}), milestone="v1.1"),
                                                 Issue(285, "closed", frozenset({"type:bug"}), "not_planned")])
        self.assertIn("but #284 is not in that release", placement_problem(node) or "")
        node.children[1] = Issue(284, "open", frozenset({"type:story"}), milestone="v1.0")
        self.assertIsNone(placement_problem(node))

    def test_a_feature_spanning_releases_has_no_milestone(self) -> None:
        node = Node(issue(259, "feature"), issue(142, "epic"),
                    [Issue(283, "open", frozenset({"type:improvement"}), milestone="v1.0"),
                     Issue(284, "open", frozenset({"type:story"}), milestone="v1.1")])
        self.assertIsNone(placement_problem(node))

    def test_two_type_labels_fail(self) -> None:
        both = Issue(5, "open", frozenset({"type:task", "type:bug"}))
        self.assertEqual(parent_problem(both, None), "Use exactly one type label, not type:bug, type:task.")

    def test_closed_untyped_and_abandoned_items_are_exempt(self) -> None:
        self.assertIsNone(parent_problem(Issue(118, "closed", frozenset(), "not_planned"), None))
        self.assertIsNone(parent_problem(issue(40, "spike", "closed", "not_planned"), None))

    def test_an_open_issue_without_a_type_label_is_flagged(self) -> None:
        problem = parent_problem(Issue(300, "open", frozenset({"ui"})), None) or ""
        self.assertIn("Give this issue exactly one type label", problem)
        self.assertIn("nothing is standalone", problem)


class CompletionRuleTests(unittest.TestCase):
    def test_each_parent_level_needs_a_completed_child(self) -> None:
        for kind in ("epic", "feature", "story", "improvement", "bug", "spike"):
            with self.subTest(kind=kind):
                self.assertIn("At least one child", completion_problem(issue(1, kind, "closed"), []) or "")

    def test_bug_closes_with_a_completed_task(self) -> None:
        self.assertIsNone(completion_problem(issue(146, "bug", "closed"), [issue(123, "task", "closed")]))

    def test_spike_closes_with_a_completed_task(self) -> None:
        self.assertIsNone(completion_problem(issue(40, "spike", "closed"), [issue(41, "task", "closed")]))

    def test_feature_accepts_stories_improvements_bugs_and_spikes(self) -> None:
        children = [issue(13, "story", "closed"), issue(144, "improvement", "closed"), issue(146, "bug", "closed"),
                    issue(40, "spike", "closed")]
        self.assertIsNone(completion_problem(issue(125, "feature", "closed"), children))

    def test_epic_needs_features_not_stories(self) -> None:
        problem = completion_problem(issue(7, "epic", "closed"), [issue(13, "story", "closed")])
        self.assertEqual(problem, "Children of an epic must be a feature: #13.")

    def test_story_rejects_an_open_task(self) -> None:
        children = [issue(57, "task", "closed"), issue(58, "task")]
        self.assertEqual(completion_problem(issue(13, "story", "closed"), children), "Close every child first: #58.")

    def test_story_rejects_a_spike_child(self) -> None:
        children = [issue(57, "task", "closed"), issue(58, "spike", "closed")]
        self.assertEqual(completion_problem(issue(13, "story", "closed"), children),
                         "Children of a story must be a task: #58.")

    def test_abandoned_children_do_not_count_as_completed(self) -> None:
        children = [issue(57, "task", "closed", "not_planned")]
        self.assertIn("must be completed", completion_problem(issue(13, "story", "closed"), children) or "")

    def test_abandoned_child_next_to_a_completed_one_passes(self) -> None:
        children = [issue(57, "task", "closed"), issue(58, "task", "closed", "not_planned")]
        self.assertIsNone(completion_problem(issue(13, "story", "closed"), children))

    def test_parents_closed_as_not_planned_stay_closed(self) -> None:
        self.assertIsNone(completion_problem(issue(13, "story", "closed", "not_planned"), []))

    def test_tasks_and_open_items_are_not_checked(self) -> None:
        self.assertIsNone(completion_problem(issue(57, "task", "closed"), []))
        self.assertIsNone(completion_problem(issue(13, "story"), []))

    def test_reads_rest_and_graphql_shapes(self) -> None:
        rest = {"number": 13, "state": "closed", "labels": [{"name": "type:story"}], "state_reason": "not_planned"}
        graph = {"number": 13, "state": "CLOSED", "labels": {"nodes": [{"name": "type:story"}]},
                 "stateReason": "COMPLETED"}
        self.assertFalse(Issue.from_api(rest).completed)
        self.assertTrue(Issue.from_api(graph).completed)

    def test_milestone_is_read_from_either_shape(self) -> None:
        rest = {"number": 13, "state": "open", "labels": [], "milestone": {"title": "v1.0"}}
        graph = {"number": 13, "state": "OPEN", "labels": {"nodes": []}, "milestone": None}
        self.assertEqual(Issue.from_api(rest).milestone, "v1.0")
        self.assertIsNone(Issue.from_api(graph).milestone)


class PullRequestTests(unittest.TestCase):
    """A pull request closes a task whose chain reaches an epic."""

    def board(self, *nodes: Node):
        by_number = {node.issue.number: node for node in nodes}
        return lambda number: by_number[number]

    def chain(self) -> list[Node]:
        epic, feature, story = issue(7, "epic"), issue(125, "feature"), issue(13, "story")
        return [Node(epic), Node(feature, epic), Node(story, feature), Node(issue(99, "task"), story)]

    def test_complete_chain_passes(self) -> None:
        self.assertIsNone(chain_problem(99, self.board(*self.chain())))

    def test_story_cannot_be_closed_by_a_pull_request(self) -> None:
        self.assertIn("#13 is a story", chain_problem(13, self.board(*self.chain())) or "")

    def test_spike_cannot_be_closed_by_a_pull_request(self) -> None:
        epic, feature = issue(7, "epic"), issue(125, "feature")
        board = self.board(Node(epic), Node(feature, epic), Node(issue(37, "spike"), feature))
        self.assertIn("#37 is a spike. A pull request closes a task only", chain_problem(37, board) or "")

    def test_task_of_a_spike_passes(self) -> None:
        epic, feature, spike = issue(7, "epic"), issue(125, "feature"), issue(37, "spike")
        board = self.board(Node(epic), Node(feature, epic), Node(spike, feature), Node(issue(41, "task"), spike))
        self.assertIsNone(chain_problem(41, board))

    def test_orphan_task_fails(self) -> None:
        self.assertIn("#100 needs a parent story, improvement, bug or spike",
                      chain_problem(100, self.board(Node(issue(100, "task")))) or "")

    def test_story_without_feature_fails(self) -> None:
        epic, story = issue(7, "epic"), issue(13, "story")
        board = self.board(Node(epic), Node(story, epic), Node(issue(99, "task"), story))
        self.assertIn("#13 needs a parent feature", chain_problem(99, board) or "")

    def test_reads_closing_lines_before_the_first_heading_only(self) -> None:
        body = "Closes #159\r\ncloses #160  \nRefs #158\n\n## What changed\nCloses #999\n"
        self.assertEqual(closing_numbers(body), [159, 160])


class DependencyRuleTests(unittest.TestCase):
    def test_a_cycle_is_reported_on_each_member(self) -> None:
        cycles = [[325, 326]]
        self.assertIn("#325 -> #326 -> #325", prerequisite_problem(Node(issue(325, "task")), cycles) or "")
        self.assertIsNone(prerequisite_problem(Node(issue(327, "task")), cycles))

    def test_a_canceled_prerequisite_is_reported(self) -> None:
        node = Node(issue(328, "task"), prerequisites=[issue(324, "task", "closed"),
                                                        issue(327, "task", "closed", "not_planned")])
        self.assertIn("Its prerequisite #327 was closed without being completed", prerequisite_problem(node, []) or "")

    def test_completed_and_open_prerequisites_pass_and_closed_items_are_exempt(self) -> None:
        node = Node(issue(328, "task"), prerequisites=[issue(324, "task", "closed"), issue(327, "task")])
        self.assertIsNone(prerequisite_problem(node, []))
        closed = Node(issue(328, "task", "closed"), prerequisites=[issue(327, "task", "closed", "not_planned")])
        self.assertIsNone(prerequisite_problem(closed, [[328, 329]]))


class GuardTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.object(project_hierarchy, "gh", return_value="")
        self.gh = patcher.start()
        self.addCleanup(patcher.stop)
        self.guard = Guard("owner/repo")

    def calls(self) -> list[tuple[str, ...]]:
        return [call.args for call in self.gh.call_args_list]

    def test_orphan_gets_the_label_and_one_comment(self) -> None:
        self.guard.check_parent(Node(issue(100, "task")))
        self.assertEqual(self.calls()[0], ("issue", "edit", "100", "--repo", "owner/repo", "--add-label", NEEDS_PARENT))
        self.assertEqual(self.calls()[1][:3], ("issue", "comment", "100"))

    def test_flagged_orphan_is_not_commented_again(self) -> None:
        self.guard.check_parent(Node(issue(100, "task", "open", None, NEEDS_PARENT)))
        self.assertEqual(self.calls(), [])

    def test_fixed_item_loses_the_label(self) -> None:
        self.guard.check_parent(Node(issue(100, "task", "open", None, NEEDS_PARENT), issue(13, "story")))
        self.assertEqual(self.calls(), [("issue", "edit", "100", "--repo", "owner/repo", "--remove-label", NEEDS_PARENT)])

    def test_new_orphan_gets_ten_minutes_to_find_its_parent(self) -> None:
        now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
        guard = Guard("owner/repo", now)
        young = Issue(160, "open", frozenset({"type:task"}), None, now - timedelta(minutes=9))
        guard.check_parent(Node(young))
        self.assertEqual(self.calls(), [])
        old = Issue(160, "open", frozenset({"type:task"}), None, now - timedelta(minutes=11))
        guard.check_parent(Node(old))
        self.assertEqual(self.calls()[0][-1], NEEDS_PARENT)

    def test_new_item_without_its_contract_gets_the_label_once_its_grace_has_passed(self) -> None:
        created = ADOPTED + timedelta(hours=1)
        guard = Guard("owner/repo", created + timedelta(minutes=11))
        guard.check_contract(Node(Issue(400, "open", frozenset({"type:task"}), None, created, "## Parent\n#13\n")))
        self.assertEqual(self.calls()[0][-1], NEEDS_CONTRACT)
        self.assertIn("missing: Purpose, Scope", self.calls()[1][-1])

    def test_item_from_before_adoption_is_left_to_the_migration(self) -> None:
        old = Issue(13, "open", frozenset({"type:story"}), None, ADOPTED - timedelta(days=3), "")
        self.guard.check_contract(Node(old))
        self.assertEqual(self.calls(), [])

    def test_dependency_problem_is_flagged(self) -> None:
        self.guard.check_dependencies(Node(issue(325, "task")), [[325, 326]])
        self.assertEqual(self.calls()[0][-1], DEPENDENCY_PROBLEM)

    def test_release_closed_without_its_record_is_reopened(self) -> None:
        self.gh.return_value = '[{"number": 1, "title": "v9.9"}]'
        self.guard.root = Path(__file__).resolve().parents[2]
        self.guard.check_releases()
        self.assertEqual(self.calls()[1], ("api", "-X", "PATCH", "repos/owner/repo/milestones/1", "-f", "state=open"))

    def test_reopened_child_reopens_its_parent_in_the_same_run(self) -> None:
        task, story = issue(57, "task", "closed"), issue(13, "story", "closed")
        # The guard reopened task #57 earlier in this run, so the story must not stay closed above it.
        self.guard.reopened.add(57)
        self.guard.check_completion(Node(story, issue(125, "feature"), [task]))
        self.assertEqual(self.calls()[0][:3], ("issue", "reopen", "13"))
        self.assertIn(13, self.guard.reopened)


if __name__ == "__main__":
    unittest.main()
