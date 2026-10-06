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
  add-iteration {"dry_run": true, "field": "Sprint", "title": "Sprint 3", "start_date": "2026-11-03"}
                                                     adds an iteration ("duration" in days defaults to the field's)
  set-options  {"dry_run": true, "field": "Area", "options": [{"name": "Security", "from": "Platform"}]}
                                                     makes the listed options the field's options, keeping the ids of
                                                     options kept or renamed ("from"); "remove_used": true allows
                                                     removing options that items still use

Values are option names, iteration titles, numbers, ISO dates, text, or null to clear. An iteration title resolves to
the current or a future iteration first; a title shared by two current or future iterations, or only by completed
ones, is refused. Nothing from the payload reaches a shell: every call passes values to `gh` as separate arguments,
GraphQL variables or a JSON request body.

Field changes keep every item's value: options and iterations are sent with their ids when GitHub's schema accepts
them, and the bridge reads the items back afterwards and sets again any value the change dropped.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field as dataclass_field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

OPERATIONS = ("dump-config", "read-items", "preflight", "report", "set-fields", "add-iteration", "set-options")
BEGIN, END = "BOARD-RESULT-BEGIN", "BOARD-RESULT-END"
MAX_CHANGES = 200

CONFIG_QUERY = """query($org: String!, $number: Int!) { organization(login: $org) { projectV2(number: $number) {
  id title url
  fields(first: 50) { nodes {
    ... on ProjectV2FieldCommon { id name dataType }
    ... on ProjectV2SingleSelectField { options { id name color description } }
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
UPDATE_FIELD = """mutation($input: UpdateProjectV2FieldInput!) {
  updateProjectV2Field(input: $input) { projectV2Field { ... on ProjectV2FieldCommon { id name } } } }"""
INPUT_FIELDS = """query($name: String!) { __type(name: $name) { inputFields { name
  type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } }"""
OPTION_INPUT = "ProjectV2SingleSelectFieldOptionInput"
ITERATION_CONFIGURATION_INPUT = "ProjectV2IterationFieldConfigurationInput"
COLORS = ("GRAY", "BLUE", "GREEN", "YELLOW", "ORANGE", "RED", "PINK", "PURPLE")
MAX_OPTIONS = 50
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
    ambiguous: frozenset[str] = dataclass_field(default_factory=frozenset)

    @classmethod
    def from_api(cls, node: dict) -> Field | None:
        if "name" not in node:
            return None
        choices = {option["name"]: option["id"] for option in node.get("options") or []}
        configuration = node.get("configuration") or {}
        current, ambiguous = iteration_titles(configuration.get("iterations") or [])
        completed, ambiguous_completed = iteration_titles(configuration.get("completedIterations") or [])
        ambiguous |= {title for title in ambiguous_completed if title not in current}
        choices.update({title: ident for title, ident in completed.items() if title not in current})
        choices.update(current)
        return cls(node["id"], node["name"], node["dataType"], choices, frozenset(ambiguous))

    def resolve(self, value: Any) -> str | None:
        """Turns a payload value into the string `gh` sends, or None to clear the field."""
        if value is None:
            return None
        if self.data_type in ("SINGLE_SELECT", "ITERATION"):
            if isinstance(value, str) and value in self.ambiguous:
                raise BridgeError(f"{self.name}: {value!r} names more than one iteration; rename one in the "
                                  f"Project's settings.")
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


def iteration_titles(iterations: list[dict]) -> tuple[dict[str, str], set[str]]:
    """Maps each title to its iteration id, and returns the titles that more than one iteration carries."""
    titles: dict[str, str] = {}
    duplicates: set[str] = set()
    for iteration in iterations:
        if iteration["title"] in titles:
            duplicates.add(iteration["title"])
        titles[iteration["title"]] = iteration["id"]
    return {title: ident for title, ident in titles.items() if title not in duplicates}, duplicates


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


def check_keys(payload: dict, required: set[str], optional: set[str]) -> None:
    missing, unknown = required - set(payload), set(payload) - required - optional
    if missing or unknown:
        raise BridgeError(f"Payload keys: missing {sorted(missing)}, unknown {sorted(unknown)}.")


def dry_run_flag(payload: dict) -> bool:
    dry_run = payload.get("dry_run", True)
    if not isinstance(dry_run, bool):
        raise BridgeError("dry_run must be true or false.")
    return dry_run


def text(value: Any, name: str, limit: int = 100) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or value != value.strip():
        raise BridgeError(f"{name} must be text of 1 to {limit} characters without surrounding spaces: {value!r}.")
    return value


def unwrap(kind: dict) -> dict:
    """The named type inside NON_NULL and LIST wrappers of an introspection type reference."""
    while kind.get("ofType"):
        kind = kind["ofType"]
    return kind


Runner = Callable[..., str]


def run_gh(*arguments: str) -> str:
    result = subprocess.run(["gh", *arguments], check=True, capture_output=True, text=True, encoding="utf-8")
    return result.stdout


class Board:
    """The Project, read once per run, and the calls that change it."""

    def __init__(self, org: str, number: int, repository: str, gh: Runner = run_gh) -> None:
        self.org, self.number, self.repository, self.gh = org, number, repository, gh
        self.diagnostics: dict[str, int] = {}
        self.load()

    def load(self) -> None:
        """Reads the Project's fields and views; called again after a field change."""
        project = self.graphql(CONFIG_QUERY, org=self.org, number=self.number)["organization"]["projectV2"]
        if project is None:
            raise BridgeError(f"Project {self.number} of {self.org} is not visible to the bridge's App.")
        self.project = project
        self.fields = {field.name: field for node in project["fields"]["nodes"]
                       if (field := Field.from_api(node)) is not None}

    def graphql(self, query: str, **variables: str | int) -> dict:
        arguments = ["api", "graphql", "-f", f"query={query}"]
        for name, value in variables.items():
            arguments += ["-F" if isinstance(value, int) else "-f", f"{name}={value}"]
        return self.answer(self.gh(*arguments))

    def graphql_body(self, query: str, variables: dict) -> dict:
        """Sends nested variables (input objects) as a JSON request body, which `-f` and `-F` can't express."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
            json.dump({"query": query, "variables": variables}, handle)
        try:
            return self.answer(self.gh("api", "graphql", "--input", handle.name))
        finally:
            os.unlink(handle.name)

    @staticmethod
    def answer(output: str) -> dict:
        response = json.loads(output)
        if response.get("errors"):
            messages = "; ".join(error.get("message", str(error)) for error in response["errors"])
            raise BridgeError(f"GitHub answered with errors: {messages}")
        return response["data"]

    def node(self, name: str, data_type: str) -> dict:
        field = self.fields.get(name)
        if field is None or field.data_type != data_type:
            fitting = sorted(key for key, value in self.fields.items() if value.data_type == data_type)
            raise BridgeError(f"{name!r} is not a {data_type} field; the Project has {fitting}.")
        return next(node for node in self.project["fields"]["nodes"] if node.get("id") == field.id)

    def input_fields(self, type_name: str) -> dict[str, dict]:
        found = self.graphql(INPUT_FIELDS, name=type_name)["__type"]
        if not found:
            raise BridgeError(f"GitHub's schema has no {type_name}; the field can't be changed through the API.")
        return {entry["name"]: entry["type"] for entry in found["inputFields"]}

    def accepts_ids(self, type_name: str) -> bool:
        return "id" in self.input_fields(type_name)

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

    def usage(self, name: str, items: dict[int, dict] | None = None) -> dict[int, str]:
        """Each issue's current value of a field, by option name or iteration title."""
        items = self.items() if items is None else items
        return {number: item["fields"][name] for number, item in items.items() if name in item["fields"]}

    def change_field(self, name: str, update: dict, before: dict[int, str], renamed: dict[str, str]) -> dict:
        """Sends a field update, then reads the items back and sets again every value the update dropped."""
        self.graphql_body(UPDATE_FIELD, {"input": {"fieldId": self.fields[name].id, **update}})
        self.load()
        field = self.fields[name]
        items = self.items()
        after = self.usage(name, items)
        restored, cleared = [], []
        for number, old in sorted(before.items()):
            wanted = renamed.get(old, old)
            if after.get(number) == wanted:
                continue
            if wanted not in field.choices or wanted in field.ambiguous:
                cleared.append({"issue": number, "value": old})
                continue
            self.write(items[number]["item"], field, field.choices[wanted])
            restored.append({"issue": number, "value": wanted})
        return {"restored": restored, "cleared": cleared}

    def add_iteration(self, payload: dict) -> dict:
        check_keys(payload, {"field", "title", "start_date"}, {"dry_run", "duration"})
        dry_run = dry_run_flag(payload)
        name, title = text(payload["field"], "field"), text(payload["title"], "title")
        configuration = self.node(name, "ITERATION")["configuration"]
        duration = payload.get("duration", configuration["duration"])
        if isinstance(duration, bool) or not isinstance(duration, int) or not 1 <= duration <= 56:
            raise BridgeError(f"duration must be a whole number of days from 1 to 56: {duration!r}.")
        try:
            start = date.fromisoformat(str(payload["start_date"]))
        except ValueError as error:
            raise BridgeError(f"start_date {payload['start_date']!r} is not an ISO date.") from error
        existing = configuration.get("iterations", []) + configuration.get("completedIterations", [])
        end = start + timedelta(days=duration)
        for iteration in existing:
            other = date.fromisoformat(iteration["startDate"])
            if iteration["title"] == title:
                raise BridgeError(f"{name} already has an iteration titled {title!r} ({iteration['startDate']}).")
            if start < other + timedelta(days=iteration["duration"]) and other < end:
                raise BridgeError(f"{title!r} from {start} for {duration} days overlaps {iteration['title']!r} "
                                  f"from {iteration['startDate']}.")
        new = {"title": title, "startDate": start.isoformat(), "duration": duration}
        result: dict[str, Any] = {"dry_run": dry_run, "field": name, "add": new,
                                  "keep": [{key: iteration[key] for key in ("id", "title", "startDate", "duration")}
                                           for iteration in existing]}
        if dry_run:
            return result
        iteration_type = unwrap(self.input_fields(ITERATION_CONFIGURATION_INPUT)["iterations"])["name"]
        with_ids = self.accepts_ids(iteration_type)
        iterations = [{**({"id": iteration["id"]} if with_ids else {}),
                       **{key: iteration[key] for key in ("title", "startDate", "duration")}} for iteration in existing]
        iterations = sorted(iterations + [new], key=lambda iteration: iteration["startDate"])
        before = self.usage(name)
        update = {"iterationConfiguration": {"startDate": iterations[0]["startDate"],
                                             "duration": configuration["duration"], "iterations": iterations}}
        result.update(self.change_field(name, update, before, {}), ids_sent=with_ids)
        configuration = self.node(name, "ITERATION")["configuration"]
        result["iterations"] = configuration.get("iterations", []) + configuration.get("completedIterations", [])
        return result

    def set_options(self, payload: dict) -> dict:
        check_keys(payload, {"field", "options"}, {"dry_run", "remove_used"})
        dry_run = dry_run_flag(payload)
        remove_used = payload.get("remove_used", False)
        if not isinstance(remove_used, bool):
            raise BridgeError("remove_used must be true or false.")
        name = text(payload["field"], "field")
        current = {option["name"]: option for option in self.node(name, "SINGLE_SELECT")["options"]}
        raw = payload["options"]
        if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_OPTIONS:
            raise BridgeError(f"options must be a list of 1 to {MAX_OPTIONS} options.")
        options, renamed, sources = [], {}, set()
        for entry in raw:
            if not isinstance(entry, dict):
                raise BridgeError(f"Each option is an object: {entry!r}.")
            check_keys(entry, {"name"}, {"from", "color", "description"})
            option_name = text(entry["name"], "name")
            source = text(entry.get("from", option_name), "from")
            old = current.get(source)
            if "from" in entry and old is None:
                raise BridgeError(f"{name} has no option {source!r} to rename; it has {sorted(current)}.")
            if old is not None and source in sources:
                raise BridgeError(f"Option {source!r} is kept twice.")
            color = entry.get("color", (old or {}).get("color", "GRAY"))
            if color not in COLORS:
                raise BridgeError(f"color must be one of {COLORS}: {color!r}.")
            description = entry.get("description", (old or {}).get("description") or "")
            if not isinstance(description, str) or len(description) > 300:
                raise BridgeError(f"description must be text of at most 300 characters: {description!r}.")
            if old is not None:
                sources.add(source)
                if source != option_name:
                    renamed[source] = option_name
            options.append({"id": (old or {}).get("id"), "name": option_name, "color": color,
                            "description": description})
        names = [option["name"] for option in options]
        if len(set(names)) != len(names):
            raise BridgeError(f"Option names must be unique: {names}.")
        before = self.usage(name)
        removed = sorted(set(current) - sources)
        in_use = {option: sorted(number for number, value in before.items() if value == option) for option in removed}
        in_use = {option: numbers for option, numbers in in_use.items() if numbers}
        result: dict[str, Any] = {"dry_run": dry_run, "field": name, "options": options, "renamed": renamed,
                                  "removed": removed, "removed_in_use": in_use}
        if dry_run:
            return result
        if in_use and not remove_used:
            raise BridgeError(f"Removing options still in use would clear their items: {in_use}. Rename them with "
                              f"\"from\", or pass \"remove_used\": true.")
        if not self.accepts_ids(OPTION_INPUT):
            raise BridgeError(f"GitHub's {OPTION_INPUT} takes no option id, so every item would lose its {name}; "
                              f"nothing was changed.")
        sent = [{key: value for key, value in option.items() if value is not None} for option in options]
        kept = {number: value for number, value in before.items() if value not in in_use}
        result.update(self.change_field(name, {"singleSelectOptions": sent}, kept, renamed))
        result["options_after"] = self.node(name, "SINGLE_SELECT")["options"]
        return result


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
    if operation == "add-iteration":
        return board.add_iteration(payload), True
    if operation == "set-options":
        return board.set_options(payload), True
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
