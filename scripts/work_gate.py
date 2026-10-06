"""The agent preflight and board report of the Work Management and Delivery Specification.

Author: Gihed Annabi
Date: 2026-10-02
Purpose: check the rules that need the GitHub Project's fields (Sprint, Status, Delivery Stage, Story Points), which
the built-in GITHUB_TOKEN can't read on a Project. It runs before every
execution and at the start of every agent session (specification sections 8, 17, 18 and 22, ADR-0001).
Ported from AnnabiGihed/RaidManager. Here the Project belongs to the Pivot-Softwares organization, and the board
bridge (scripts/board_bridge.py, .github/workflows/board.yml) runs this module with a GitHub App installation token
(specification section 22, A11), because the agent works from cloud sessions.

Usage: work_gate.py preflight <task>        the section 8 gate; exits 1 and names each failed condition
       work_gate.py report [--apply-labels]  board report; exits 1 on any violation; --apply-labels maintains the
                                             scheduling-violation label
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from project_hierarchy import closing_numbers
from work_contracts import (BUG, EPIC, FEATURE, IMPROVEMENT, SPIKE, STORY, TASK, missing_sections,
                            task_milestone_problem, unknown_sections)

REPOSITORY = os.environ.get("BOARD_REPOSITORY", "Pivot-Softwares/VPS-Configuration")
PROJECT = os.environ.get("BOARD_PROJECT_ID", "")
TIMEZONE = ZoneInfo("Europe/Brussels")
SPRINTS = Path("docs/planning/sprints")
RELEASES = Path("docs/planning/releases")
SCHEDULING_VIOLATION = "scheduling-violation"
OUTCOMES = frozenset({STORY, IMPROVEMENT, BUG, SPIKE})
EXECUTABLE = OUTCOMES | {TASK}
TYPES = frozenset({EPIC, FEATURE, STORY, IMPROVEMENT, BUG, SPIKE, TASK})
EXECUTING = frozenset({"In Progress", "In Review"})


@dataclass(frozen=True)
class Sprint:
    title: str
    start: date
    duration: int

    def window(self) -> tuple[datetime, datetime]:
        """Local midnight boundaries in Europe/Brussels, start inclusive and end exclusive (sections 7, 22)."""
        start = datetime.combine(self.start, datetime.min.time(), TIMEZONE)
        end = datetime.combine(self.start + timedelta(days=self.duration), datetime.min.time(), TIMEZONE)
        return start, end

    def active(self, now: datetime) -> bool:
        start, end = self.window()
        return start <= now < end


@dataclass
class Item:
    number: int
    title: str
    state: str
    reason: str | None
    labels: frozenset[str]
    body: str = ""
    milestone: str | None = None
    assignees: tuple[str, ...] = ()
    parent: int | None = None
    prerequisites: list[tuple[int, str, str | None]] = field(default_factory=list)
    status: str | None = None
    stage: str | None = None
    points: float | None = None
    sprint: Sprint | None = None

    @property
    def kind(self) -> str | None:
        kinds = sorted(self.labels & TYPES)
        return kinds[0] if len(kinds) == 1 else None

    @property
    def completed(self) -> bool:
        return self.state == "closed" and self.reason in (None, "completed")

    @property
    def canceled(self) -> bool:
        return self.state == "closed" and not self.completed


@dataclass(frozen=True)
class Finding:
    rule: str
    passed: bool
    detail: str


def sprint_state(sprint: Sprint, root: Path) -> str | None:
    """Reads the state from the sprint's record, docs/planning/sprints/sprint-NN.md, if it exists."""
    digits = "".join(character for character in sprint.title if character.isdigit())
    if not digits:
        return None
    path = root / SPRINTS / f"sprint-{int(digits):02d}.md"
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] == "State":
            return cells[1]
    return None


def sequence_rows(text: str) -> list[str]:
    """Returns the table rows of a release record's Sprint sequence section."""
    rows: list[str] = []
    in_sequence = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_sequence = line.strip() == "## Sprint sequence"
        elif in_sequence and line.startswith("|"):
            rows.append(line)
    return rows


def row_sprint(row: str) -> str | None:
    """Reads "Sprint N" from a sequence row's first cell, plain or linked; None for the header and divider."""
    first = row.strip("|").split("|")[0]
    digits = "".join(character for character in first.split("](")[0] if character.isdigit())
    return f"Sprint {int(digits)}" if "Sprint" in first and digits else None


def sprint_releases(root: Path) -> dict[str, str]:
    """Maps each sprint to its release, from the Sprint sequence section of each release record (owner rule, #346)."""
    found: dict[str, str] = {}
    for record in sorted((root / RELEASES).glob("*.md")):
        for row in sequence_rows(record.read_text(encoding="utf-8")):
            sprint = row_sprint(row)
            if sprint:
                found[sprint] = record.stem
    return found


def sprint_release_problem(item: Item, releases: dict[str, str]) -> str | None:
    """A sprint's items share its release (owner rule, #346)."""
    if item.sprint is None:
        return None
    release = releases.get(item.sprint.title)
    if release is None:
        return f"{item.sprint.title} belongs to no release record in {RELEASES}."
    if item.milestone != release:
        return (f"#{item.number} is on release {item.milestone or 'none'}, but {item.sprint.title} belongs to "
                f"{release}; a sprint's items share its release.")
    return None


def contract_gaps(item: Item | None) -> list[str]:
    if item is None:
        return []
    kind = item.kind
    if kind is None:
        return ["exactly one type label"]
    return missing_sections(kind, item.body) + [f"{name} (Unknown)" for name in unknown_sections(kind, item.body)]


def completed(state: str, reason: str | None) -> bool:
    return state == "closed" and reason in (None, "completed")


def sprint_name(item: Item) -> str:
    return item.sprint.title if item.sprint else "no sprint"


def same_sprint(first: Item | None, second: Item) -> bool:
    return bool(first and first.sprint and second.sprint and first.sprint.title == second.sprint.title)


def hierarchy_problem(task: Item, parent: Item | None) -> str | None:
    if task.kind != TASK:
        return f"#{task.number} is not a task; only tasks are executed (outcome items run through their tasks)."
    if parent is None or parent.kind not in OUTCOMES:
        return f"#{task.number} has no story, improvement, bug or spike parent on the Project."
    gaps = contract_gaps(task) + contract_gaps(parent)
    return f"Contract gaps: {', '.join(gaps)}." if gaps else None


def active_sprint_problem(task: Item, now: datetime, root: Path) -> str | None:
    if task.sprint is None:
        return "No sprint is assigned."
    state = sprint_state(task.sprint, root)
    if state is None:
        return f"{task.sprint.title} has no record in {SPRINTS}."
    if state.lower() == "canceled":
        return f"{task.sprint.title} is canceled."
    if task.sprint.active(now):
        return None
    start, end = task.sprint.window()
    return (f"{task.sprint.title} runs from {start:%Y-%m-%d %H:%M} to {end:%Y-%m-%d %H:%M} Europe/Brussels "
            f"(end exclusive); now is {now.astimezone(TIMEZONE):%Y-%m-%d %H:%M}.")


def matching_sprint_problem(task: Item, parent: Item | None) -> str | None:
    if parent is None or same_sprint(parent, task):
        return None
    return f"#{task.number} is in {sprint_name(task)} but its parent #{parent.number} is in {sprint_name(parent)}."


def open_problem(task: Item, parent: Item | None) -> str | None:
    if task.state == "closed":
        return f"#{task.number} is already {'completed' if task.completed else 'canceled'}."
    if parent and parent.state == "closed":
        return f"Its parent #{parent.number} is closed."
    return None


def preflight(task: Item, items: dict[int, Item], now: datetime, root: Path) -> list[Finding]:
    """The seven conditions of the active-sprint gate (section 8) for one task."""
    parent = items.get(task.parent) if task.parent else None
    missing = [name for name, value in (("assignee", task.assignees), ("Delivery Stage", task.stage)) if not value]
    waiting = [f"#{number}" for number, state, reason in task.prerequisites if not completed(state, reason)]
    checks = (
        ("1. Hierarchy and contract", hierarchy_problem(task, parent),
         "Fix them with work-classification-and-hierarchy and work-backlog-refinement."),
        ("2. Active sprint", active_sprint_problem(task, now, root),
         "Ask the owner to select the work into an active sprint; never move dates."),
        ("3. Matching sprint", matching_sprint_problem(task, parent),
         "Select the task and its parent into the same sprint."),
        ("4. Matching release",
         (task_milestone_problem(task.milestone, parent.number, parent.milestone) if parent else None)
         or sprint_release_problem(task, sprint_releases(root)),
         "Align the milestones (specification section 15) and the sprint's release."),
        ("5. Assignee and Delivery Stage", f"Missing: {', '.join(missing)}." if missing else None,
         "Set them on the task."),
        ("6. Prerequisites", f"Not completed yet: {', '.join(waiting)}." if waiting else None,
         "Wait for their completion evidence."),
        ("7. Open and not canceled", open_problem(task, parent),
         "Reopen it deliberately (work-task-execution-and-completion) first."),
    )
    return [Finding(rule, problem is None, f"{problem} {fix}" if problem else "ok") for rule, problem, fix in checks]


def status_problem(item: Item) -> str | None:
    """Closure reason against Project Status (specification section 13, A4)."""
    if item.completed and item.status != "Done":
        return f"#{item.number} is closed as completed but its Status is {item.status or 'empty'}, not Done."
    if item.canceled and item.status != "Canceled":
        return f"#{item.number} is closed as not planned but its Status is {item.status or 'empty'}, not Canceled."
    if item.state == "open" and item.status in ("Done", "Canceled"):
        return f"#{item.number} is open but its Status is {item.status}."
    return None


SCHEDULING = "Scheduling violations"
MISMATCHES = "Status and closure mismatches"
UNESTIMATED = "Unestimated selected stories"
SELECTED_GAPS = "Ready or selected items with contract gaps"
UNAVAILABLE = "Unavailable prerequisites"
UNEXPLAINED_BLOCKS = "Blocked items without a recorded reason"
SPRINT_RELEASE = "Sprint and release mismatches"
BACKLOG_GAPS = "Open items with contract gaps (allowed in Backlog)"
VIOLATIONS = (SCHEDULING, MISMATCHES, SPRINT_RELEASE, UNESTIMATED, SELECTED_GAPS, UNAVAILABLE, UNEXPLAINED_BLOCKS)
Findings = dict[str, list[tuple[int, str]]]


def scheduling_findings(item: Item, parent: Item | None) -> list[str]:
    found: list[str] = []
    if item.kind in EXECUTABLE and item.status in EXECUTING and item.sprint is None:
        found.append(f"Status {item.status} but no sprint was ever assigned.")
    if item.kind == TASK and parent and parent.kind in OUTCOMES and item.sprint and not same_sprint(parent, item):
        found.append(f"In {sprint_name(item)}, but its parent #{parent.number} is in {sprint_name(parent)}.")
    return found


def unavailable_prerequisites(item: Item, items: dict[int, Item]) -> list[str]:
    if item.sprint is None:
        return []
    return [f"#{number}" for number, state, reason in item.prerequisites
            if not completed(state, reason) and not same_sprint(items.get(number), item)]


def check_open_item(item: Item, items: dict[int, Item], found: Findings) -> None:
    parent = items.get(item.parent) if item.parent else None
    found[SCHEDULING] += [(item.number, detail) for detail in scheduling_findings(item, parent)]
    if item.kind == STORY and item.sprint and item.points is None:
        found[UNESTIMATED].append((item.number, f"Selected into {sprint_name(item)}."))
    gaps = contract_gaps(item)
    if gaps:
        found[SELECTED_GAPS if item.status == "Ready" or item.sprint else BACKLOG_GAPS].append(
            (item.number, ", ".join(gaps)))
    outside = unavailable_prerequisites(item, items)
    if outside:
        found[UNAVAILABLE].append(
            (item.number, f"Waits on {', '.join(outside)}, unfinished and outside {sprint_name(item)}."))
    if item.status == "Blocked" and "unblock" not in item.body.lower():
        found[UNEXPLAINED_BLOCKS].append(
            (item.number, "Record the reason, the person responsible and the unblock condition."))


def report(items: dict[int, Item], open_pull_requests: list[tuple[int, str]], now: datetime,
           releases: dict[str, str]) -> Findings:
    """Every board finding the specification asks validators for (sections 17 and 18), grouped by category."""
    found: Findings = {category: [] for category in (*VIOLATIONS, BACKLOG_GAPS)}
    for item in sorted(items.values(), key=lambda value: value.number):
        problem = status_problem(item)
        if problem:
            found[MISMATCHES].append((item.number, problem))
        mismatch = sprint_release_problem(item, releases)
        if mismatch:
            found[SPRINT_RELEASE].append((item.number, mismatch))
        if item.state == "open" and item.kind is not None:
            check_open_item(item, items, found)
    found[SCHEDULING] += pull_request_findings(items, open_pull_requests, now)
    return found


def pull_request_findings(items: dict[int, Item], open_pull_requests: list[tuple[int, str]],
                          now: datetime) -> list[tuple[int, str]]:
    """An open pull request for a task without an active sprint may not change or merge (A5)."""
    found: list[tuple[int, str]] = []
    for number, body in open_pull_requests:
        for task_number in closing_numbers(body):
            task = items.get(task_number)
            if task and (task.sprint is None or not task.sprint.active(now)):
                found.append((task_number, f"Pull request #{number} is open, but the task has no active sprint; it "
                                           "may not change or merge until the task is selected into one (A5)."))
    return found


def gh(*arguments: str) -> str:
    result = subprocess.run(["gh", *arguments], check=True, capture_output=True, text=True, encoding="utf-8")
    return result.stdout


ITEMS_QUERY = """query($cursor: String) { node(id: "%s") { ... on ProjectV2 { items(first: 100, after: $cursor) {
  pageInfo { hasNextPage endCursor }
  nodes {
    status: fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
    stage: fieldValueByName(name: "Delivery Stage") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
    points: fieldValueByName(name: "Story Points") { ... on ProjectV2ItemFieldNumberValue { number } }
    sprint: fieldValueByName(name: "Sprint") { ... on ProjectV2ItemFieldIterationValue { title startDate duration } }
    type content { ... on Issue { number title state stateReason body milestone { title }
      labels(first: 20) { nodes { name } } assignees(first: 10) { nodes { login } } parent { number }
      blockedBy(first: 50) { nodes { number state stateReason } } } }
  } } } } }"""


def item_from_api(node: dict) -> Item | None:
    content = node.get("content") or {}
    if node.get("type") == "REDACTED" or (node.get("type") == "ISSUE" and "number" not in content):
        # GitHub hides the issue when the reader can't access its repository (#21); never treat it as absent.
        raise SystemExit("A Project item is hidden from this reader: its repository isn't accessible to the "
                         "pivot-board-bridge installation, so eligibility is unknown (specification section 18).")
    if "number" not in content:
        return None
    sprint = node.get("sprint")
    return Item(
        number=content["number"], title=content["title"], state=content["state"].lower(),
        reason=(content.get("stateReason") or "").lower() or None,
        labels=frozenset(label["name"] for label in content["labels"]["nodes"]), body=content.get("body") or "",
        milestone=(content.get("milestone") or {}).get("title"),
        assignees=tuple(person["login"] for person in content["assignees"]["nodes"]),
        parent=(content.get("parent") or {}).get("number"),
        prerequisites=[(other["number"], other["state"].lower(), (other.get("stateReason") or "").lower() or None)
                       for other in content["blockedBy"]["nodes"]],
        status=(node.get("status") or {}).get("name"), stage=(node.get("stage") or {}).get("name"),
        points=(node.get("points") or {}).get("number"),
        sprint=Sprint(sprint["title"], date.fromisoformat(sprint["startDate"]), sprint["duration"]) if sprint else None,
    )


def project_id() -> str:
    """The Project's node id, given by the board bridge in BOARD_PROJECT_ID."""
    project = os.environ.get("BOARD_PROJECT_ID") or PROJECT
    if not project:
        raise SystemExit("BOARD_PROJECT_ID is not set; run this through the board bridge.")
    return project


def fetch_items() -> dict[int, Item]:
    items: dict[int, Item] = {}
    cursor = ""
    while True:
        arguments = (["api", "graphql", "-f", f"query={ITEMS_QUERY % project_id()}"]
                     + (["-f", f"cursor={cursor}"] if cursor else []))
        response = json.loads(gh(*arguments))
        if response.get("errors"):
            raise SystemExit(f"GitHub answered with errors: {response['errors']}")
        page = response["data"]["node"]["items"]
        for node in page["nodes"]:
            item = item_from_api(node)
            if item:
                items[item.number] = item
        if not page["pageInfo"]["hasNextPage"]:
            return items
        cursor = page["pageInfo"]["endCursor"]


def fetch_open_pull_requests() -> list[tuple[int, str]]:
    found = json.loads(gh("pr", "list", "--repo", REPOSITORY, "--state", "open", "--json", "number,body",
                          "--limit", "100"))
    return [(value["number"], value["body"] or "") for value in found]


def apply_labels(items: dict[int, Item], violations: set[int]) -> None:
    """Keeps the scheduling-violation label on exactly the items the report flags (section 17)."""
    for item in items.values():
        has = SCHEDULING_VIOLATION in item.labels
        if item.number in violations and not has:
            gh("issue", "edit", str(item.number), "--repo", REPOSITORY, "--add-label", SCHEDULING_VIOLATION)
        elif item.number not in violations and has:
            gh("issue", "edit", str(item.number), "--repo", REPOSITORY, "--remove-label", SCHEDULING_VIOLATION)


def run_preflight(number: int, items: dict[int, Item], now: datetime, root: Path) -> int:
    task = items.get(number)
    if task is None:
        print(f"FAIL #{number} is not on the Project; eligibility is unknown (section 18).")
        return 1
    findings = preflight(task, items, now, root)
    for finding in findings:
        print(f"{'PASS' if finding.passed else 'FAIL'} {finding.rule}: {finding.detail}")
    return 0 if all(finding.passed for finding in findings) else 1


def run_report(items: dict[int, Item], now: datetime, labels: bool) -> int:
    for item in items.values():
        if item.status == "Blocked":
            # The reason, the person responsible and the unblock condition are usually a comment (section 11).
            item.body += "\n" + gh("issue", "view", str(item.number), "--repo", REPOSITORY, "--comments")
    found = report(items, fetch_open_pull_requests(), now, sprint_releases(Path.cwd()))
    for category, entries in found.items():
        print(f"## {category} ({len(entries)})")
        for number, detail in entries:
            print(f"- #{number}: {detail}")
        print()
    if labels:
        apply_labels(items, {number for number, _ in found[SCHEDULING]})
    return 1 if any(found[category] for category in VIOLATIONS) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    gate = commands.add_parser("preflight", help="check the active-sprint gate for one task")
    gate.add_argument("task", type=int)
    board = commands.add_parser("report", help="report every board finding")
    board.add_argument("--apply-labels", action="store_true", help="maintain the scheduling-violation label")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    items = fetch_items()
    if args.command == "preflight":
        return run_preflight(args.task, items, now, Path.cwd())
    return run_report(items, now, args.apply_labels)


if __name__ == "__main__":
    sys.exit(main())
