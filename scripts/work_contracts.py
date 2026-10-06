"""Rules of the Work Management and Delivery Specification that read only issues, milestones and files.

Author: Gihed Annabi
Date: 2026-10-02
Purpose: shared by the hierarchy guard (scripts/project_hierarchy.py, run with GITHUB_TOKEN) and the agent preflight,
so both apply the same contract, milestone, dependency and release-record rules
(docs/reference/work-management-specification.md, ADR-0001). Ported from AnnabiGihed/RaidManager.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

EPIC, FEATURE, STORY, IMPROVEMENT, BUG, SPIKE, TASK = (
    "type:epic", "type:feature", "type:story", "type:improvement", "type:bug", "type:spike", "type:task")

# VPS-Configuration adopted the specification on 2026-10-06 (A12), before its first work item, so every item
# meets the contract.
ADOPTED = datetime(2026, 10, 5, 22, 0, 0, tzinfo=timezone.utc)
UNKNOWN = "unknown: needs clarification"
EMPTY_ANSWERS = {"", "_no response_", "none yet", "tbd", "to be created"}
HEADING = re.compile(r"^#{2,3}[ \t]+(\S.*)$")

# Section 4: what every item contains, then what each type adds. Each requirement lists the headings that satisfy it,
# so a form asks once for, say, "Acceptance criteria" and that also states the completion conditions.
Requirement = tuple[str, tuple[str, ...]]
ACCEPTANCE_CRITERIA, CAPABILITY_BOUNDARIES = "Acceptance criteria", "Capability boundaries"
EXECUTION_SCOPE = "Execution scope"
EXIT_CRITERIA, SUCCESS_MEASURES, VERIFICATION_METHOD = "Exit criteria", "Success measures", "Verification method"


def heading(name: str) -> Requirement:
    """A requirement answered by the heading of the same name."""
    return name, (name,)


COMMON: tuple[Requirement, ...] = (
    ("Purpose", ("Purpose", "Objective", "Benefit")),
    ("Scope", ("Scope", EXECUTION_SCOPE, CAPABILITY_BOUNDARIES)),
    ("Completion conditions", ("Completion conditions", ACCEPTANCE_CRITERIA, EXIT_CRITERIA, SUCCESS_MEASURES)),
    heading("Dependencies"),
    ("Verification", ("Verification", VERIFICATION_METHOD)),
)
PARENT = heading("Parent")
BY_TYPE: dict[str, tuple[Requirement, ...]] = {
    EPIC: (heading("Objective"), heading(SUCCESS_MEASURES)),
    FEATURE: (heading(CAPABILITY_BOUNDARIES), heading("Expected outcomes")),
    STORY: (heading("User"), heading("Need"), heading("Benefit"), heading(ACCEPTANCE_CRITERIA)),
    IMPROVEMENT: (heading("Current situation"), heading("Desired enhancement"), heading(VERIFICATION_METHOD)),
    BUG: (heading("Expected behavior"), heading("Actual behavior"), heading("Reproduction steps"),
          heading("Affected environment")),
    SPIKE: (heading("Research question"), heading("Timebox"), heading(EXIT_CRITERIA),
            heading("Findings or decision deliverable")),
    TASK: (heading("Bounded deliverable"), heading(EXECUTION_SCOPE), heading("Delivery Stage"),
           heading(VERIFICATION_METHOD)),
}


def sections(body: str) -> dict[str, str]:
    """Maps each level-2 or level-3 heading, lowercased, to the text under it."""
    found: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []
    for line in body.replace("\r\n", "\n").split("\n"):
        match = HEADING.match(line)
        if match:
            if current is not None:
                found[current] = "\n".join(lines).strip()
            current, lines = match.group(1).rstrip("# \t").lower(), []
        elif current is not None:
            lines.append(line)
    if current is not None:
        found[current] = "\n".join(lines).strip()
    return found


def requirements(kind: str) -> tuple[Requirement, ...]:
    return (() if kind == EPIC else (PARENT,)) + COMMON + BY_TYPE[kind]


def missing_sections(kind: str, body: str) -> list[str]:
    """Returns the section 4 requirements the body doesn't answer; an "Unknown: needs clarification" answer counts."""
    found = sections(body)
    missing: list[str] = []
    for name, headings in requirements(kind):
        answers = [found[heading.lower()] for heading in headings if heading.lower() in found]
        if not any(answer.strip().lower() not in EMPTY_ANSWERS for answer in answers):
            missing.append(name)
    return missing


def unknown_sections(kind: str, body: str) -> list[str]:
    """Returns the requirements still answered "Unknown: needs clarification"; such an item can't become Ready (A7)."""
    found = sections(body)
    return [name for name, headings in requirements(kind)
            if any(answers_unknown(found.get(heading.lower(), "")) for heading in headings)]


def answers_unknown(text: str) -> bool:
    """A line, or list item, that starts with the marker; a sentence that only quotes the marker doesn't count."""
    return any(line.strip().lstrip("-* ").lower().startswith(UNKNOWN) for line in text.splitlines())


def contract_problem(kind: str | None, state: str, created_at: datetime | None, body: str) -> str | None:
    """Section 4 for open items created since adoption; older open items are backfilled by the migration (A7)."""
    if kind is None or state != "open" or created_at is None or created_at < ADOPTED:
        return None
    missing = missing_sections(kind, body)
    if not missing:
        return None
    return (f"The issue contract (specification section 4) is missing: {', '.join(missing)}. Add each as a heading "
            "with its content, or `Unknown: needs clarification` when it isn't known yet.")


def task_milestone_problem(task_milestone: str | None, parent_number: int, parent_milestone: str | None) -> str | None:
    """A task shares its parent's release milestone (specification section 15, A2)."""
    if task_milestone == parent_milestone:
        return None
    return (f"This task's milestone is {shown(task_milestone)} but its parent #{parent_number}'s is "
            f"{shown(parent_milestone)}; a task shares its parent's release milestone (specification section 15).")


def scope_milestone_problem(milestone: str | None, children: list[tuple[int, str | None]]) -> str | None:
    """A feature or epic has a milestone only when its entire delivery scope belongs to that release (A2)."""
    if milestone is None:
        return None
    outside = [f"#{number}" for number, child_milestone in children if child_milestone != milestone]
    if not outside:
        return None
    return (f"It carries milestone {shown(milestone)}, but {', '.join(outside)} is not in that release. A feature or "
            "epic has a milestone only when its entire scope belongs to that release; otherwise remove its milestone "
            "(specification section 15).")


def shown(milestone: str | None) -> str:
    return f"`{milestone}`" if milestone else "none"


def canceled_prerequisites(prerequisites: list[tuple[int, str, str | None]]) -> list[int]:
    """Returns prerequisites closed as not planned, which aren't satisfied without an owner decision (section 10)."""
    return [number for number, state, reason in prerequisites
            if state == "closed" and (reason or "completed") not in ("completed",)]


def dependency_cycles(blocked_by: dict[int, list[int]]) -> list[list[int]]:
    """Returns each dependency cycle once, as the numbers along it, smallest first (section 10 rejects cycles)."""
    cycles: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    state: dict[int, int] = {}
    path: list[int] = []

    def visit(number: int) -> None:
        state[number] = 1
        path.append(number)
        for prerequisite in blocked_by.get(number, []):
            if state.get(prerequisite) == 1:
                cycle = path[path.index(prerequisite):]
                start = cycle.index(min(cycle))
                ordered = tuple(cycle[start:] + cycle[:start])
                if ordered not in seen:
                    seen.add(ordered)
                    cycles.append(list(ordered))
            elif prerequisite not in state:
                visit(prerequisite)
        path.pop()
        state[number] = 2

    for number in sorted(blocked_by):
        if number not in state:
            visit(number)
    return cycles


RELEASED = re.compile(r"state\W+released\b", re.IGNORECASE)
DELIVERY_DATE = re.compile(r"actual delivery date\W+\d{4}-\d{2}-\d{2}", re.IGNORECASE)


def release_record_problem(record: str | None) -> str | None:
    """A release closes only after its record shows it Released with an actual delivery date (sections 6, 13)."""
    if record is None:
        return "its release record is missing"
    if not RELEASED.search(record):
        return "its release record doesn't show the state Released"
    if not DELIVERY_DATE.search(record):
        return "its release record has no actual delivery date"
    return None
