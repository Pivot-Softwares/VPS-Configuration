# Project automation

The [VPS Configuration Project](https://github.com/orgs/Pivot-Softwares/projects/1) applies the
[Work Management and Delivery Specification](work-management-specification.md)
([ADR-0001](../adr/0001-adopt-the-raidmanager-work-process.md)). It is the owner's copy of the
[Raid Manager Project](https://github.com/users/AnnabiGihed/projects/2), so its fields and views follow RaidManager's
[project automation](https://github.com/AnnabiGihed/RaidManager/blob/main/docs/reference/project-automation.md). This
page documents what differs and what automation enforces here; the specification is the authority for the rules.

## Hierarchy

Every item sits in one chain of native sub-issues, Epic → Feature → User Story, Improvement, Bug or Spike → Task, with
exactly one `type:` label (specification §2, §3, §15). The issue forms in `.github/ISSUE_TEMPLATE/` set the label and
ask for the parent; add the new issue as a sub-issue of that parent at once. Blank issues are disabled.

## Fields

The copy carries RaidManager's fields: Status (Backlog, Ready, In Progress, In Review, Blocked, Done, Canceled),
Delivery Stage, Sprint (two-week iterations), Story Points, Priority (P0 Critical to P3 Later), Risk, Start date,
Target date and Area. Their ids are recorded in the `vps-board-operations` skill from the board bridge's
`dump-config`. Area still holds RaidManager's product areas; its values for this repository are an owner decision.

## Board bridge

The agent works from Claude Code cloud sessions, where GitHub GraphQL is blocked, so the `board` workflow
(`.github/workflows/board.yml`, `scripts/board_bridge.py`) reads and writes the Project's fields for it
(specification §22, A11).

> ⚠️ **Credential:** the `pivot-board-bridge` GitHub App's private key, the environment secret
> `BOARD_APP_PRIVATE_KEY` of the `board` environment (deployment branches: `main` only), with the App's client id in
> the environment variable `BOARD_APP_CLIENT_ID`. Grants, through a token that expires after one hour and is revoked
> when the job ends: Issues read and write and Pull requests read on this repository, and the organization's Projects
> read and write. Expires: never. Rotation: none needed; generate a new key and delete the old one on the App's page
> if it may have leaked. Revocation: the App's settings page, Private keys. Why it is needed: GitHub Projects can't be
> read or written with the built-in token, and personal access tokens are forbidden.

| Operation | What it does |
| --- | --- |
| `dump-config` | Prints the Project's fields with their option and iteration ids, and its views. |
| `read-items` | Prints each issue's Project item id and field values. |
| `preflight` | Runs the active-sprint gate for a task (`scripts/work_gate.py`); the run fails on any failed condition. |
| `report` | Runs the board report and keeps the `scheduling-violation` label current. |
| `set-fields` | Sets or clears field values by name, as a dry run by default, skipping values already set. |

The workflow runs only from `main`, one run at a time, and validates every payload against the Project's own fields
before it writes anything. Payload values never reach a shell or a query's text.

## Rules enforced by the hierarchy guard

The `project-hierarchy` workflow (`scripts/project_hierarchy.py`), ported from RaidManager without its mockup rule,
runs with the built-in token on every issue change and every 15 minutes:

- **Parent:** exactly one type label, a parent of the allowed type, and none for an epic; otherwise `needs-parent`.
- **Contract:** every heading of specification §4, or `Unknown: needs clarification`; otherwise `needs-contract`.
- **Dependencies** (audit only): a cycle or a canceled prerequisite gets `dependency-problem`.
- **Completion:** a parent closed as completed is reopened until every child is closed and at least one is completed.
- **Releases:** a release milestone closed before its record shows Released with a delivery date is reopened.

The workflow also creates the seven `type:` labels and the rule labels if they are missing. A new issue gets
10 minutes before it is flagged.

## One-time setup

These steps are the owner's, in the browser, because neither API can make them:

1. **App permissions:** on the `pivot-board-bridge` App's settings page, add **Pull requests: Read** (the board report
   lists open pull requests), save, and accept the new permission on the organization's installation page.
2. **App client id:** copy the App's **Client ID** from its settings page into a variable `BOARD_APP_CLIENT_ID` of the
   `board` environment. It isn't secret. `BOARD_APP_ID` can stay or go; the workflow no longer reads it.
3. **Project workflows:** in the Project's **Workflows**, keep **Item closed** and **Item reopened** off, **Auto-close
   issue**, **Item added to project** (Status `Backlog`) and **Auto-add sub-issues to project** on, and turn on
   **Auto-add to project** for `Pivot-Softwares/VPS-Configuration` with the filter `is:issue`.
4. **Sprint field:** in the Project's **Settings → Sprint**, make the iterations two weeks long and add **Sprint 1**
   starting 2026-10-06. RaidManager's past iterations, copied with the Project, can be removed there.

## Verify

1. Run `board` with `dump-config`: the result lists the fields and views, and `Sprint 1` among the iterations.
2. Create a test issue from the task form without a parent: within 25 minutes it carries `needs-parent`.
3. Close it as not planned: the next audit removes the label.
