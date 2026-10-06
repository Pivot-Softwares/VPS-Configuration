---
name: vps-board-operations
description: >-
  Mandatory recipes for operating the VPS-Configuration GitHub Project from a cloud session: the board bridge workflow
  and its operations, the field and option ids, creating and linking work items, setting fields, starting, handing
  over and closing work in the right order, bulk changes with a dry run and read-back, and the pitfalls inherited from
  RaidManager. Use it with the work-* skills, which hold the rules; this skill holds the commands.
---

# VPS-Configuration board operations

The work-* skills and the [Work Management and Delivery
Specification](../../../docs/reference/work-management-specification.md) say what must happen; this skill says how
to do it on this board. It mirrors `raidmanager-board-operations`, with one difference: RaidManager reads and writes
its Project with the owner's local `gh` login, while this repository's agent runs in Claude Code cloud sessions, where
GitHub GraphQL is blocked. Project fields therefore go through the **board bridge** (spec §22, A11).

## The board bridge

> ⚠️ **Credential:** the `pivot-board-bridge` GitHub App's private key, stored only as the secret
> `BOARD_APP_PRIVATE_KEY` of the `board` environment (deployments from `main` only), with the App id in the variable
> `BOARD_APP_ID`. It never expires and needs no rotation; each run exchanges it for an installation token that expires
> after one hour. The App is installed on this repository only, with Issues read and write, Metadata read and
> organization Projects read and write (`credentials-policy`).

- **Workflow:** `.github/workflows/board.yml`, started by `workflow_dispatch` on `main`. Start it with the GitHub
  tools (`actions_run_trigger`, method `run_workflow`, workflow `board.yml`, ref `main`) and read its result from the
  job log (`get_job_logs`): the result is one JSON document between the lines `BOARD-RESULT-BEGIN` and
  `BOARD-RESULT-END`, also shown in the run summary.
- **Inputs:** `operation` and `payload` (a JSON string). The script accepts only the operations below, validates the
  payload against the Project's own field names and option names, and never passes input to a shell.

| Operation | Payload | Result |
| --- | --- | --- |
| `dump-config` | `{}` | Project id, fields with option and iteration ids, views with layout and filter. |
| `read-items` | `{"issues": [12, 13]}` or `{}` for all | Each item's Project item id and field values. |
| `preflight` | `{"task": 12}` | PASS or FAIL for each of the seven gate conditions (spec §8), with the correction; the job fails on any FAIL. |
| `report` | `{"apply_labels": true}` | The board report of `work-board-configuration-and-validation`; keeps `scheduling-violation` current. |
| `set-fields` | `{"dry_run": true, "changes": [{"issue": 12, "field": "Status", "value": "In Progress"}]}` | Each change, `skipped` when already set; adds an issue to the Project first if needed. Values are option names, iteration titles, numbers, ISO dates or `null` to clear. |

- **Dry run first** for every `set-fields` call that changes more than one item, then apply with `"dry_run": false` and
  read back with `read-items`.
- Until the bridge is on `main`, no Project field can be changed from a session. Say so and give the owner the exact
  values to set in the browser instead.

## Ids

Organization `Pivot-Softwares`, repository `Pivot-Softwares/VPS-Configuration`, Project: **not recorded yet** (the
owner's copy of the Raid Manager Project). Fill this table from the first `dump-config` and keep it current; re-read
it if a call fails with an unknown id. The bridge works by names, so the ids here are for checking, not for typing.

| Field | Field id | Values (option or iteration id) |
| --- | --- | --- |
| Status | to fill | Backlog, Ready, In Progress, In Review, Blocked, Done, Canceled |
| Sprint | to fill | two-week iterations (spec §22) |
| Delivery Stage | to fill | Business Analysis, Functional Analysis, Architecture Analysis, Development, Testing, Deployment |
| Story Points | to fill | a number |
| Risk | to fill | Low, Medium, High |
| Priority | to fill | P0 Critical, P1 High, P2 Normal, P3 Later |
| Area | to fill | to be agreed with the owner: the copy carries RaidManager's product areas |
| Start date | to fill | a date |
| Target date | to fill | a date |

## Recipes

Issues, labels, milestones, sub-issues and dependencies are repository data: change them with the GitHub tools
(`issue_write`, `sub_issue_write`, `add_issue_comment`) or repository-scoped REST calls (`gh api
repos/Pivot-Softwares/VPS-Configuration/...`). Only Project fields need the bridge. Write any multi-step change as a
short Python script in the scratchpad that is safe to rerun.

### Create a work item

1. Classify it first (`work-classification-and-hierarchy`) and pick its parent.
2. Write the body with exactly the headings of its issue form in `.github/ISSUE_TEMPLATE/` (`### Parent`,
   `### Purpose`, and so on), with LF line endings. Record what the owner decided under
   `### Owner decisions (<date>, recorded here)`.
3. Create it with its `type:` label, milestone and assignee `AnnabiGihed`, titled `<Type>: <title>`.
4. Link the parent at once with the child's database id (not its number):
   `gh api -X POST repos/Pivot-Softwares/VPS-Configuration/issues/<parent>/sub_issues -F sub_issue_id=<child id>`.
5. Set its fields with `set-fields`: Status, Sprint, Delivery Stage, Priority, Area and, for outcome items, Story Points
   and Risk.
6. Record the estimate and the risk as comments on outcome items:
   `Estimate: **3 Story Points**. Rationale: ... Estimated by the agent (specification sections 9 and 22).` and
   `Risk: **Low**. Reason: ... (agent assessment; the owner may change it).`
7. Dependencies are native links:
   `gh api -X POST repos/Pivot-Softwares/VPS-Configuration/issues/<n>/dependencies/blocked_by -F issue_id=<blocker id>`.

### Start work

1. Run `preflight` for the task. A new item can be missing from the Project for a minute: wait and run it again.
   Never change dates or sprints to pass a failing gate.
2. Set the task `In Progress`, check its assignee, and set its Start date to today in Europe/Brussels. Do the same for
   each parent up to the epic that has no actual start yet.
3. Branch from `origin/main` as `feature/<task>-<slug>` or `fix/<task>-<slug>` only.

### Hand over

1. Open the draft pull request. Its prose names other items without a closing keyword: never write close, closes,
   closed, fix, fixes, fixed, resolve, resolves or resolved right before an issue number, except in the one
   `Closes #<task>` line.
2. A few seconds after opening, check that GitHub linked exactly the task (`closingIssuesReferences`). If not, edit
   the description and check again before anything else.
3. Set the task `In Review` and draft both review comments (`vps-github-project-workflow`).

### Close after a merge

1. Confirm the merge with the GitHub tools (`state` `MERGED`, `mergedAt` inside the task's active sprint, A5). Never
   clean up on the owner's word alone.
2. Clean up the branches (`vps-github-project-workflow`).
3. **Comment first, then set Done.** The Project closes an issue as soon as its Status becomes Done, so post the
   evidence comment before setting the Target date to the closing day and Status `Done`.
4. Check the issue is closed as completed; close it if not.
5. Validate the parents independently (`work-task-execution-and-completion`) and close each with its own evidence.
6. Run `report` and report its blocking categories.

### Bulk changes

1. Read the items with `read-items`.
2. **Dry run:** compute every change and look at the counts and exceptions before writing.
3. Apply, skipping values already set, so a rerun after a failure is safe.
4. **Read back** and post the read-back on the item that asked for the change.

## Pitfalls inherited from RaidManager

| Pitfall | Fix |
| --- | --- |
| A body with CRLF line endings broke the guard's heading parsing. | Write bodies with LF; replace `\r\n` with `\n` before editing a body read back. |
| Setting Status to Done closed the issue before its evidence comment was posted. | Comment first, then set Done. |
| Single-select options recreated without their ids wiped every item's value. | Update options with their existing ids (`work-board-configuration-and-validation`). |
| A creation script ran twice after a partial failure and made duplicates. | Read the open issues first, reuse an item whose title exists, skip links that already exist. |
| Adding an item to the Project raced the Project's "Auto-add sub-issues" workflow. | Retry with growing waits; the add is idempotent. |
| A description said a merge "closed" an issue; GitHub linked it and the Project set it back to In Progress. | Keep closing keywords out of prose; check `closingIssuesReferences`. |
| Two handed-over pull requests: the second fell behind `main` after the first merged. | Hand over one at a time or state the merge order. |
| A task verified outside the repository (a run on the server) closed on merge, before its verification. | Say to merge only after the verification; if it merges first, reopen the task as Blocked with the unblock condition and close it again with the evidence. |
| Planning records drifted from the board. | Generate item lists in records from `read-items`, never by hand. |

## Sources

- `AnnabiGihed/RaidManager`: `raidmanager-board-operations`, `docs/reference/project-automation.md`.
- Spec §8, §11, §13, §15 and §22 (A11); [ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md).
