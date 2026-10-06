"""Keep the work items in one Epic -> Feature -> Story/Improvement/Bug/Spike -> Task hierarchy.

Ported from AnnabiGihed/RaidManager without its mockup rule (this repository has no user interface).
The rules come from the Work Management and Delivery Specification (ADR-0001) and are all checked with the built-in
GITHUB_TOKEN; the rules that need Project fields run in the agent preflight instead (specification section 22):

- Parent: every item has exactly one type label and, except an epic, a parent of the level above; an epic has none.
  A task shares its parent's milestone; a feature or epic has a milestone only when all its children are in that
  release (section 15, A2). Nothing is standalone. A violation adds the needs-parent label and one explanatory
  comment; fixing the item removes the label.
- Contract: an open item created since adoption answers every section 4 heading, or gets needs-contract.
- Type: an open item with one type label carries the matching organization issue type, or gets type-mismatch. The rule
  waits until the repository offers that issue type, so it stays quiet before the board bridge creates the types.
- Dependencies (audit only): a dependency cycle, or an open item waiting on a canceled prerequisite, gets
  dependency-problem (section 10).
- Releases (audit and milestone events): a release milestone closed before its record shows it Released with a
  delivery date is reopened (sections 6 and 13).
- Completion: an epic, feature, story, improvement, bug or spike closed as completed is reopened unless at least one
  child of the level below is completed and every child is closed.
- Pull requests: each "Closes #N" names a task whose chain reaches an epic.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from work_contracts import (BUG, EPIC, FEATURE, IMPROVEMENT, ISSUE_TYPES, SPIKE, STORY, TASK, canceled_prerequisites,
                            contract_problem, dependency_cycles, release_record_problem, scope_milestone_problem,
                            task_milestone_problem)


NEEDS_PARENT = "needs-parent"
NEEDS_CONTRACT = "needs-contract"
DEPENDENCY_PROBLEM = "dependency-problem"
TYPE_MISMATCH = "type-mismatch"
RELEASES = Path("docs/planning/releases")
# A new issue usually gets its parent a moment after it is created, so the parent rule waits before flagging it.
GRACE = timedelta(minutes=10)
# A spike is a peer of stories, improvements and bugs under a feature, and has tasks like them (ADR-0025).
WORK_ITEMS = frozenset({TASK})
BACKLOG_ITEMS = frozenset({STORY, IMPROVEMENT, BUG, SPIKE})
# Allowed parent types and child types for each type label.
PARENTS: dict[str, frozenset[str]] = {
    EPIC: frozenset(),
    FEATURE: frozenset({EPIC}),
    **dict.fromkeys(BACKLOG_ITEMS, frozenset({FEATURE})),
    **dict.fromkeys(WORK_ITEMS, BACKLOG_ITEMS),
}
CHILDREN: dict[str, frozenset[str]] = {
    EPIC: frozenset({FEATURE}),
    FEATURE: BACKLOG_ITEMS,
    **dict.fromkeys(BACKLOG_ITEMS, WORK_ITEMS),
}
# Type names in hierarchy order.
NAMES = {kind: kind.removeprefix("type:") for kind in (EPIC, FEATURE, STORY, IMPROVEMENT, BUG, SPIKE, TASK)}
# Leaves first, so a parent is judged after the children the same run reopened.
DEPTH = {TASK: 0, **dict.fromkeys(BACKLOG_ITEMS, 1), FEATURE: 2, EPIC: 3}
ANCESTOR_LEVELS = 3
CLOSING_LINE = re.compile(r"^Closes #(\d+)[ \t]*$", re.IGNORECASE)
FIELDS = ("number state stateReason createdAt milestone { title } issueType { name } "
          "labels(first: 20) { nodes { name } }")
NODE = (f"{FIELDS} body parent {{ {FIELDS} }} subIssues(first: 100) {{ nodes {{ {FIELDS} }} }} "
        f"blockedBy(first: 50) {{ nodes {{ {FIELDS} }} }}")


@dataclass(frozen=True)
class Issue:
    number: int
    state: str
    labels: frozenset[str]
    state_reason: str | None = None
    created_at: datetime | None = None
    body: str = ""
    milestone: str | None = None
    issue_type: str | None = None

    @classmethod
    def from_api(cls, value: dict) -> Issue:
        """Reads an issue from the REST (lists of label objects, type) or GraphQL (labels.nodes, issueType) shape."""
        labels = value["labels"]
        names = labels["nodes"] if isinstance(labels, dict) else labels
        reason = value.get("state_reason") or value.get("stateReason") or ""
        created = value.get("created_at") or value.get("createdAt")
        milestone = value.get("milestone") or {}
        issue_type = value.get("type") or value.get("issueType") or {}
        return cls(value["number"], value["state"].lower(), frozenset(label["name"] for label in names),
                   reason.lower() or None,
                   datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None,
                   value.get("body") or "", milestone.get("title"), issue_type.get("name"))

    @property
    def kinds(self) -> list[str]:
        return sorted(label for label in self.labels if label in PARENTS)

    @property
    def kind(self) -> str | None:
        return self.kinds[0] if len(self.kinds) == 1 else None

    @property
    def completed(self) -> bool:
        # Issues closed before GitHub recorded a reason count as completed.
        return self.state == "closed" and self.state_reason in (None, "completed")

    @property
    def abandoned(self) -> bool:
        return self.state == "closed" and not self.completed


@dataclass
class Node:
    """An issue with its parent and children, as one GraphQL query returns them."""

    issue: Issue
    parent: Issue | None = None
    children: list[Issue] = field(default_factory=list)
    prerequisites: list[Issue] = field(default_factory=list)

    @classmethod
    def from_api(cls, value: dict) -> Node:
        parent = Issue.from_api(value["parent"]) if value.get("parent") else None
        children = [Issue.from_api(child) for child in value["subIssues"]["nodes"]]
        prerequisites = [Issue.from_api(item) for item in (value.get("blockedBy") or {}).get("nodes", [])]
        return cls(Issue.from_api(value), parent, children, prerequisites)


ORDER = list(NAMES)


def names(kinds: frozenset[str]) -> str:
    """Lists type names in hierarchy order: "story, improvement or bug"."""
    ordered = [NAMES[kind] for kind in sorted(kinds, key=ORDER.index)]
    return ordered[0] if len(ordered) == 1 else ", ".join(ordered[:-1]) + " or " + ordered[-1]


def a(text: str) -> str:
    """Prefixes the indefinite article: "an epic", "a feature"."""
    return f"{'an' if text[:1] in 'aeiou' else 'a'} {text}"


def numbers(issues: list[Issue]) -> str:
    return ", ".join(f"#{issue.number}" for issue in issues)


def parent_problem(issue: Issue, parent: Issue | None) -> str | None:
    """Returns why an item is misplaced in the hierarchy, or None when it is placed correctly."""
    if len(issue.kinds) > 1:
        return f"Use exactly one type label, not {', '.join(issue.kinds)}."
    kind = issue.kind
    if issue.abandoned or (kind is None and issue.state != "open"):
        return None
    if kind is None:
        return (f"Give this issue exactly one type label ({', '.join(ORDER)}) and link it to its parent; "
                "nothing is standalone.")
    allowed = PARENTS[kind]
    if not allowed:
        return None if parent is None else f"An epic has no parent: remove it from #{parent.number}."
    if parent is None:
        return f"Add this {NAMES[kind]} as a sub-issue of {a(names(allowed))}."
    if parent.kind not in allowed:
        found = NAMES.get(parent.kind or "", "item without one type label")
        return f"Its parent #{parent.number} is {a(found)}; {a(NAMES[kind])} belongs under {a(names(allowed))}."
    if kind == TASK:
        return task_milestone_problem(issue.milestone, parent.number, parent.milestone)
    return None


def placement_problem(node: Node) -> str | None:
    """The parent rule, then the milestone a feature or epic may carry for its scope (A2)."""
    problem = parent_problem(node.issue, node.parent)
    if problem or node.issue.abandoned or node.issue.kind not in (FEATURE, EPIC):
        return problem
    children = [(child.number, child.milestone) for child in node.children if not child.abandoned]
    return scope_milestone_problem(node.issue.milestone, children)


def prerequisite_problem(node: Node, cycles: list[list[int]]) -> str | None:
    """A dependency cycle, or an open item waiting on a canceled prerequisite (section 10)."""
    if node.issue.state != "open":
        return None
    cycle = next((cycle for cycle in cycles if node.issue.number in cycle), None)
    if cycle:
        chain = " -> ".join(f"#{number}" for number in cycle + cycle[:1])
        return f"It is part of a dependency cycle: {chain} (each blocked by the next). Remove one link."
    canceled = canceled_prerequisites([(item.number, item.state, item.state_reason) for item in node.prerequisites])
    if canceled:
        listed = ", ".join(f"#{number}" for number in canceled)
        return (f"Its prerequisite {listed} was closed without being completed. Record an owner decision that it is "
                "no longer required and remove the link, or replace it with the work that is.")
    return None


def type_problem(issue: Issue, available: frozenset[str]) -> str | None:
    """The native issue type must match the one type label, once the repository offers that type."""
    expected = ISSUE_TYPES.get(issue.kind or "")
    if issue.state != "open" or expected is None or expected not in available or issue.issue_type == expected:
        return None
    found = f"is {issue.issue_type}" if issue.issue_type else "is not set"
    return f"The label `{issue.kind}` needs the issue type {expected}, but the type {found}. Set the type to {expected}."


def completion_problem(issue: Issue, children: list[Issue]) -> str | None:
    """Returns why a completed parent may not stay closed, or None when it may."""
    kind = issue.kind
    if not issue.completed or kind not in CHILDREN:
        return None
    expected = CHILDREN[kind]
    unexpected = [child for child in children if child.kind not in expected]
    if unexpected:
        return f"Children of {a(NAMES[kind])} must be {a(names(expected))}: {numbers(unexpected)}."
    open_children = [child for child in children if child.state != "closed"]
    if open_children:
        return f"Close every child first: {numbers(open_children)}."
    if not any(child.completed for child in children):
        return f"At least one child {names(expected)} must be completed before this {NAMES[kind]} can close."
    return None


def chain_problem(number: int, fetch: Callable[[int], Node]) -> str | None:
    """Returns why a pull request may not close #number, or None when it names a correctly placed work item."""
    node = fetch(number)
    if node.issue.kind not in WORK_ITEMS:
        found = NAMES.get(node.issue.kind or "", "item without one type label")
        return f"#{number} is {a(found)}. A pull request closes a task only; use Refs for other items."
    current, expected = node, [BACKLOG_ITEMS, frozenset({FEATURE}), frozenset({EPIC})]
    for level in expected:
        if current.parent is None or current.parent.kind not in level:
            where = f"#{current.issue.number}"
            return (f"{where} needs a parent {names(level)}, so that #{number} reaches an epic through a story, "
                    "improvement, bug or spike and a feature.")
        current = fetch(current.parent.number)
    if current.parent is not None:
        return f"Epic #{current.issue.number} must not have a parent."
    return None


def closing_numbers(body: str) -> list[int]:
    """Reads the standalone "Closes #N" lines before the first section heading, as the review workflow does."""
    found: list[int] = []
    for line in body.replace("\r\n", "\n").split("\n"):
        if line.startswith("## "):
            break
        match = CLOSING_LINE.match(line.strip())
        if match:
            found.append(int(match.group(1)))
    return found


def gh(*arguments: str) -> str:
    result = subprocess.run(["gh", *arguments], check=True, capture_output=True, text=True, encoding="utf-8")
    return result.stdout


def graphql(query: str, **variables: str | int) -> dict:
    arguments = ["api", "graphql", "-f", f"query={query}"]
    for name, value in variables.items():
        arguments += ["-F" if isinstance(value, int) else "-f", f"{name}={value}"]
    return json.loads(gh(*arguments))["data"]


def fetch_node(repository: str, number: int) -> Node:
    owner, name = repository.split("/")
    query = (f"query($owner: String!, $name: String!, $number: Int!) {{ repository(owner: $owner, name: $name) "
             f"{{ issue(number: $number) {{ {NODE} }} }} }}")
    return Node.from_api(graphql(query, owner=owner, name=name, number=number)["repository"]["issue"])


def fetch_all(repository: str) -> list[Node]:
    owner, name = repository.split("/")
    query = (f"query($owner: String!, $name: String!, $cursor: String) {{ repository(owner: $owner, name: $name) "
             f"{{ issues(first: 50, after: $cursor) {{ pageInfo {{ hasNextPage endCursor }} nodes {{ {NODE} }} }} }} }}")
    nodes: list[Node] = []
    cursor = ""
    while True:
        variables = {"owner": owner, "name": name, **({"cursor": cursor} if cursor else {})}
        page = graphql(query, **variables)["repository"]["issues"]
        nodes += [Node.from_api(value) for value in page["nodes"]]
        if not page["pageInfo"]["hasNextPage"]:
            return nodes
        cursor = page["pageInfo"]["endCursor"]


class Guard:
    """Applies the rules to issues and records what it changed."""

    def __init__(self, repository: str, now: datetime | None = None, root: Path | None = None) -> None:
        self.repository = repository
        self.now = now or datetime.now(timezone.utc)
        # The checkout the workflow runs on (main), where the release records are read.
        self.root = root or Path.cwd()
        self.reopened: set[int] = set()
        self.available: frozenset[str] | None = None

    def current(self, issue: Issue) -> Issue:
        if issue.number not in self.reopened:
            return issue
        return Issue(issue.number, "open", issue.labels, None, issue.created_at, issue.body, issue.milestone,
                     issue.issue_type)

    def issue_types(self) -> frozenset[str]:
        """The enabled issue types the repository offers, read once per run."""
        if self.available is None:
            try:
                types = json.loads(gh("api", f"repos/{self.repository}/issue-types") or "[]")
            except subprocess.CalledProcessError as error:
                # The type rule must never stop the other rules: without the list it stays quiet this run.
                print(f"WARNING: the type rule is skipped, issue types could not be read: {error.stderr.strip()}")
                types = []
            self.available = frozenset(kind["name"] for kind in types if kind.get("is_enabled", True))
        return self.available

    def flag(self, issue: Issue, label: str, problem: str | None, rule: str) -> None:
        """Adds the label with one explanatory comment while the problem lasts, and removes it once it is fixed."""
        if problem and issue.created_at and self.now - issue.created_at < GRACE:
            return
        if problem and label not in issue.labels:
            gh("issue", "edit", str(issue.number), "--repo", self.repository, "--add-label", label)
            gh("issue", "comment", str(issue.number), "--repo", self.repository, "--body",
               f"{rule}: {problem} The `{label}` label goes away once it is fixed.")
            print(f"Flagged #{issue.number} {label}: {problem}")
        elif not problem and label in issue.labels:
            gh("issue", "edit", str(issue.number), "--repo", self.repository, "--remove-label", label)
            print(f"Cleared #{issue.number} {label}")

    def check_parent(self, node: Node) -> None:
        self.flag(node.issue, NEEDS_PARENT, placement_problem(node), "Hierarchy rule (specification sections 2, 15)")

    def check_contract(self, node: Node) -> None:
        issue = node.issue
        problem = None if len(issue.kinds) > 1 else contract_problem(issue.kind, issue.state, issue.created_at,
                                                                      issue.body)
        self.flag(issue, NEEDS_CONTRACT, problem, "Contract rule (specification section 4)")

    def check_type(self, node: Node) -> None:
        self.flag(node.issue, TYPE_MISMATCH, type_problem(node.issue, self.issue_types()),
                  "Type rule (specification section 15)")

    def check_dependencies(self, node: Node, cycles: list[list[int]]) -> None:
        self.flag(node.issue, DEPENDENCY_PROBLEM, prerequisite_problem(node, cycles),
                  "Dependency rule (specification section 10)")

    def check_releases(self) -> None:
        """Reopens a release milestone closed before its record shows the delivery (sections 6 and 13)."""
        milestones = json.loads(gh("api", f"repos/{self.repository}/milestones?state=closed&per_page=100"))
        for milestone in milestones:
            path = self.root / RELEASES / f"{milestone['title']}.md"
            record = path.read_text(encoding="utf-8") if path.is_file() else None
            problem = release_record_problem(record)
            if problem:
                gh("api", "-X", "PATCH", f"repos/{self.repository}/milestones/{milestone['number']}",
                   "-f", "state=open")
                print(f"Reopened milestone {milestone['title']}: {problem} ({RELEASES / (milestone['title'] + '.md')})")

    def check_completion(self, node: Node) -> None:
        issue = self.current(node.issue)
        problem = completion_problem(issue, [self.current(child) for child in node.children])
        if problem:
            gh("issue", "reopen", str(issue.number), "--repo", self.repository, "--comment",
               f"Completion rule: {problem}")
            self.reopened.add(issue.number)
            print(f"Reopened #{issue.number}: {problem}")

    def check(self, node: Node) -> None:
        self.check_parent(node)
        self.check_contract(node)
        self.check_type(node)
        self.check_completion(node)


def check_pull_request(repository: str, body: str) -> int:
    problems = [problem for number in closing_numbers(body)
                if (problem := chain_problem(number, lambda n: fetch_node(repository, n)))]
    for problem in problems:
        print(f"ERROR: {problem}")
    if not problems:
        print("Every closed task sits in the Epic, Feature, Story/Improvement/Bug/Spike and Task hierarchy.")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue", type=int, help="check one issue and its ancestors")
    parser.add_argument("--pull-request", action="store_true", help="check the work items PR_BODY closes")
    parser.add_argument("--releases", action="store_true", help="check closed release milestones only")
    args = parser.parse_args()
    if args.pull_request:
        return check_pull_request(args.repository, os.environ.get("PR_BODY", ""))
    guard = Guard(args.repository)
    if args.releases:
        guard.check_releases()
        return 0
    if args.issue:
        number: int = args.issue
        for _ in range(ANCESTOR_LEVELS + 1):
            node = fetch_node(args.repository, number)
            guard.check(node)
            if node.parent is None:
                break
            number = node.parent.number
        return 0
    nodes = fetch_all(args.repository)
    for node in sorted(nodes, key=lambda node: DEPTH.get(node.issue.kind or "", -1)):
        guard.check(node)
    open_numbers = {node.issue.number for node in nodes if node.issue.state == "open"}
    cycles = dependency_cycles({node.issue.number: [item.number for item in node.prerequisites
                                                    if item.number in open_numbers]
                                for node in nodes if node.issue.number in open_numbers})
    for node in nodes:
        guard.check_dependencies(node, cycles)
    guard.check_releases()
    return 0


if __name__ == "__main__":
    sys.exit(main())
