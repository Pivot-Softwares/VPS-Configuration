"""The board bridge: read and write the organization Project's fields from a GitHub Actions run.

Author: Gihed Annabi
Date: 2026-10-06
Purpose: the agent works from Claude Code cloud sessions, where GitHub GraphQL is blocked, so the
`board` workflow runs this script with an installation token of the `pivot-board-bridge` GitHub App
(specification section 22, A11, ADR-0001). The agent starts the workflow with an operation and a JSON payload, and
reads the result from the log between BOARD-RESULT-BEGIN and BOARD-RESULT-END.

Operations (environment OPERATION, payload in PAYLOAD):
  dump-config  {}                                    fields with option and iteration ids, and views
  read-items   {"issues": [12, 13]} or {}            Project item ids and field values
  preflight    {"task": 12}                          the active-sprint gate of work_gate.py; fails on any FAIL
  report       {"apply_labels": true}                the board report of work_gate.py
  set-fields   {"dry_run": true, "changes": [...]}   each change {"issue": 12, "field": "Status", "value": "Ready"}

Values are option names, iteration titles, numbers, ISO dates, text, or null to clear. Nothing from the payload
reaches a shell: every call passes values to `gh` as separate arguments and GraphQL variables.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

OPERATIONS = ("dump-config", "read-items", "preflight", "report", "set-fields")
BEGIN, END = "BOARD-RESULT-BEGIN", "BOARD-RESULT-END"
MAX_CHANGES = 200

CONFIG_QUERY = """query($org: String!, $number: Int!) { organization(login: $org) { projectV2(number: $number) {
  id title url
  fields(first: 50) { nodes {
    ... on ProjectV2FieldCommon { id name dataType }
    ... on ProjectV2SingleSelectField { options { id name } }
    ... on ProjectV2IterationField { configuration { duration startDay
      iterations { id title startDate duration } completedIterations { id title startDate duration } } } } }
  views(first: 50) { nodes { id number name layout filter } } } } }"""

ITEMS_QUERY = """query($project: ID!, $cursor: String) { node(id: $project) { ... on ProjectV2 {
  items(first: 100, after: $cursor) { pageInfo { hasNextPage endCursor } nodes { id
    type content { __typename ... on Issue { number repository { nameWithOwner } } }
    fieldValues(first: 30) { nodes {
      ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldIterationValue { title field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } } } } } } } } }"""

ADD_ITEM = """mutation($project: ID!, $content: ID!) {
  addProjectV2ItemById(input: {projectId: $project, contentId: $content}) { item { id } } }"""
CLEAR = """mutation($project: ID!, $item: ID!, $field: ID!) {
  clearProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item, fieldId: $field}) { projectV2Item { id } } }"""
SET = """mutation($project: ID!, $item: ID!, $field: ID!, $value: %s) {
  updateProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item, fieldId: $field,
    value: {%s: $value}}) { projectV2Item { id } } }"""
# Field data type -> (GraphQL variable type, value key, gh flag: -f sends a string, -F a number).
SETTERS = {
    "SINGLE_SELECT": ("String!", "singleSelectOptionId", "-f"),
    "ITERATION": ("String!", "iterationId", "-f"),
    "NUMBER": ("Float!", "number", "-F"),
    "DATE": ("Date!", "date", "-f"),
    "TEXT": ("String!", "text", "-f"),
}


class BridgeError(Exception):
    """A payload or configuration problem, reported to the caller instead of a traceback."""


@dataclass(frozen=True)
class Field:
    id: str
    name: str
    data_type: str
    choices: dict[str, str]

    @classmethod
    def from_api(cls, node: dict) -> Field | None:
        if "name" not in node:
            return None
        choices = {option["name"]: option["id"] for option in node.get("options") or []}
        configuration = node.get("configuration") or {}
        for iteration in configuration.get("iterations", []) + configuration.get("completedIterations", []):
            choices[iteration["title"]] = iteration["id"]
        return cls(node["id"], node["name"], node["dataType"], choices)

    def resolve(self, value: Any) -> str | None:
        """Turns a payload value into the string `gh` sends, or None to clear the field."""
        if value is None:
            return None
        if self.data_type in ("SINGLE_SELECT", "ITERATION"):
            if not isinstance(value, str) or value not in self.choices:
                raise BridgeError(f"{self.name}: {value!r} is not one of {sorted(self.choices)}.")
            return self.choices[value]
        if self.data_type == "NUMBER":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise BridgeError(f"{self.name}: {value!r} is not a number.")
            return str(value)
        if self.data_type == "DATE":
            try:
                return date.fromisoformat(str(value)).isoformat()
            except ValueError as error:
                raise BridgeError(f"{self.name}: {value!r} is not an ISO date.") from error
        if self.data_type == "TEXT":
            if not isinstance(value, str):
                raise BridgeError(f"{self.name}: {value!r} is not text.")
            return value
        raise BridgeError(f"{self.name}: fields of type {self.data_type} can't be set by the bridge.")


@dataclass(frozen=True)
class Change:
    issue: int
    field: str
    value: Any


def parse_changes(payload: dict, fields: dict[str, Field]) -> tuple[bool, list[Change]]:
    """Validates a set-fields payload against the Project's own fields before anything is written."""
    unknown = set(payload) - {"dry_run", "changes"}
    if unknown:
        raise BridgeError(f"Unknown payload keys: {sorted(unknown)}.")
    dry_run = payload.get("dry_run", True)
    if not isinstance(dry_run, bool):
        raise BridgeError("dry_run must be true or false.")
    raw = payload.get("changes")
    if not isinstance(raw, list) or not raw or len(raw) > MAX_CHANGES:
        raise BridgeError(f"changes must be a list of 1 to {MAX_CHANGES} changes.")
    changes: list[Change] = []
    for entry in raw:
        if not isinstance(entry, dict) or set(entry) != {"issue", "field", "value"}:
            raise BridgeError(f"Each change has exactly issue, field and value: {entry!r}.")
        issue, name = entry["issue"], entry["field"]
        if isinstance(issue, bool) or not isinstance(issue, int) or issue < 1:
            raise BridgeError(f"issue must be a positive number: {issue!r}.")
        if name not in fields:
            raise BridgeError(f"Unknown field {name!r}; the Project has {sorted(fields)}.")
        fields[name].resolve(entry["value"])
        changes.append(Change(issue, name, entry["value"]))
    return dry_run, changes


def issue_numbers(payload: dict, key: str) -> list[int]:
    values = payload.get(key, [])
    if not isinstance(values, list) or any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        raise BridgeError(f"{key} must be a list of issue numbers.")
    return values


Runner = Callable[..., str]


def run_gh(*arguments: str) -> str:
    result = subprocess.run(["gh", *arguments], check=True, capture_output=True, text=True, encoding="utf-8")
    return result.stdout


class Board:
    """The Project, read once per run, and the calls that change it."""

    def __init__(self, org: str, number: int, repository: str, gh: Runner = run_gh) -> None:
        self.org, self.number, self.repository, self.gh = org, number, repository, gh
        project = self.graphql(CONFIG_QUERY, org=org, number=number)["organization"]["projectV2"]
        if project is None:
            raise BridgeError(f"Project {number} of {org} is not visible to the bridge's App.")
        self.project = project
        self.diagnostics: dict[str, int] = {}
        self.fields = {field.name: field for node in project["fields"]["nodes"]
                       if (field := Field.from_api(node)) is not None}

    def graphql(self, query: str, **variables: str | int) -> dict:
        arguments = ["api", "graphql", "-f", f"query={query}"]
        for name, value in variables.items():
            arguments += ["-F" if isinstance(value, int) else "-f", f"{name}={value}"]
        response = json.loads(self.gh(*arguments))
        if response.get("errors"):
            messages = "; ".join(error.get("message", str(error)) for error in response["errors"])
            raise BridgeError(f"GitHub answered with errors: {messages}")
        return response["data"]

    def config(self) -> dict:
        return {"project": {key: self.project[key] for key in ("id", "title", "url")},
                "fields": self.project["fields"]["nodes"], "views": self.project["views"]["nodes"]}

    def items(self) -> dict[int, dict]:
        """Maps each issue number on the Project to its item id and field values by field name.

        Fails instead of skipping when GitHub hides an item's content (type REDACTED, #21): an unreadable item would
        otherwise look absent, and set-fields and the gate would act on a wrong picture of the board.
        """
        found: dict[int, dict] = {}
        self.diagnostics = {}
        redacted = 0
        cursor = ""
        while True:
            variables: dict[str, str | int] = {"project": self.project["id"]}
            if cursor:
                variables["cursor"] = cursor
            page = self.graphql(ITEMS_QUERY, **variables)["node"]["items"]
            for node in page["nodes"]:
                kind = node.get("type") or "UNKNOWN"
                self.diagnostics[kind] = self.diagnostics.get(kind, 0) + 1
                if kind == "REDACTED" or (kind == "ISSUE" and not (node.get("content") or {}).get("number")):
                    redacted += 1
                    continue
                number = (node.get("content") or {}).get("number")
                if number is None:
                    continue
                values = {}
                for value in node["fieldValues"]["nodes"]:
                    name = (value.get("field") or {}).get("name")
                    if name:
                        values[name] = next(value[key] for key in ("name", "title", "number", "date", "text")
                                            if key in value)
                found[number] = {"item": node["id"], "fields": values}
            if not page["pageInfo"]["hasNextPage"]:
                break
            cursor = page["pageInfo"]["endCursor"]
        if redacted:
            raise BridgeError(
                f"{redacted} of {sum(self.diagnostics.values())} Project items are hidden from the "
                f"pivot-board-bridge App (item types {self.diagnostics}). GitHub hides an item's issue when the App's "
                f"installation can't access its repository: give the installation access to {self.repository}.")
        return found

    def add(self, number: int) -> str:
        """Adds an issue of the repository to the Project; GitHub returns the existing item when it is there."""
        node_id = json.loads(self.gh("api", f"repos/{self.repository}/issues/{number}"))["node_id"]
        return self.graphql(ADD_ITEM, project=self.project["id"], content=node_id)["addProjectV2ItemById"]["item"]["id"]

    def write(self, item: str, field: Field, value: str | None) -> None:
        if value is None:
            self.graphql(CLEAR, project=self.project["id"], item=item, field=field.id)
            return
        variable_type, key, flag = SETTERS[field.data_type]
        arguments = ["api", "graphql", "-f", f"query={SET % (variable_type, key)}",
                     "-f", f"project={self.project['id']}", "-f", f"item={item}", "-f", f"field={field.id}",
                     flag, f"value={value}"]
        self.gh(*arguments)

    def set_fields(self, payload: dict) -> dict:
        dry_run, changes = parse_changes(payload, self.fields)
        items = self.items()
        results = []
        for change in changes:
            field = self.fields[change.field]
            current = items.get(change.issue, {}).get("fields", {}).get(change.field)
            if current == change.value or (field.data_type == "NUMBER" and current is not None
                                            and change.value is not None and float(current) == float(change.value)):
                results.append({**change.__dict__, "result": "skipped"})
                continue
            if not dry_run:
                item = items.get(change.issue, {}).get("item") or self.add(change.issue)
                items.setdefault(change.issue, {"item": item, "fields": {}})["fields"][change.field] = change.value
                self.write(item, field, field.resolve(change.value))
            results.append({**change.__dict__, "from": current, "result": "would set" if dry_run else "set"})
        return {"dry_run": dry_run, "changes": results}


def gate(operation: str, payload: dict) -> tuple[dict, bool]:
    """Runs work_gate's preflight or report and returns its printed findings."""
    import work_gate

    now = datetime.now(timezone.utc)
    items = work_gate.fetch_items()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        if operation == "preflight":
            task = payload.get("task")
            if isinstance(task, bool) or not isinstance(task, int):
                raise BridgeError("preflight needs {\"task\": <issue number>}.")
            code = work_gate.run_preflight(task, items, now, Path.cwd())
        else:
            apply_labels = payload.get("apply_labels", False)
            if not isinstance(apply_labels, bool):
                raise BridgeError("apply_labels must be true or false.")
            code = work_gate.run_report(items, now, apply_labels)
    return {"passed": code == 0, "output": output.getvalue()}, code == 0


def run(operation: str, payload: dict, board_factory: Callable[[], Board]) -> tuple[dict, bool]:
    if operation not in OPERATIONS:
        raise BridgeError(f"Unknown operation {operation!r}; use one of {', '.join(OPERATIONS)}.")
    board = board_factory()
    if operation == "dump-config":
        return board.config(), True
    if operation == "read-items":
        wanted = issue_numbers(payload, "issues")
        items = board.items()
        return {"items": {str(number): value for number, value in sorted(items.items())
                          if not wanted or number in wanted},
                "item_types": board.diagnostics}, True
    if operation == "set-fields":
        return board.set_fields(payload), True
    os.environ["BOARD_PROJECT_ID"] = board.project["id"]
    return gate(operation, payload)


def emit(result: dict) -> None:
    text = json.dumps(result, indent=2, sort_keys=True, default=str)
    print(BEGIN)
    print(text)
    print(END)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"## Board bridge: {os.environ.get('OPERATION', '')}\n\n```json\n{text}\n```\n")


def main() -> int:
    operation = os.environ.get("OPERATION", "")
    try:
        payload = json.loads(os.environ.get("PAYLOAD") or "{}")
        if not isinstance(payload, dict):
            raise BridgeError("The payload must be a JSON object.")
        org, number = os.environ["BOARD_ORG"], int(os.environ["BOARD_PROJECT_NUMBER"])
        repository = os.environ["BOARD_REPOSITORY"]
        result, passed = run(operation, payload, lambda: Board(org, number, repository))
    except (BridgeError, json.JSONDecodeError, KeyError, ValueError) as error:
        emit({"error": str(error)})
        return 1
    except subprocess.CalledProcessError as error:
        emit({"error": f"gh failed: {error.stderr.strip()}"})
        return 1
    emit(result)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
