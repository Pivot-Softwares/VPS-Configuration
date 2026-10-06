---
name: work-board-configuration-and-validation
description: >-
  Use when changing the GitHub Project (fields, Status values, views, built-in workflows), labels, issue forms, the
  hierarchy guard or the work preflight and report, or when configuring Azure DevOps from the specification's mapping;
  also when running the board report.
---

# Board configuration and validation

The [Work Management and Delivery Specification](../../../docs/reference/work-management-specification.md) is the
authority; this skill applies it. Board visibility doesn't equal enforcement (spec §18).

## Triggers

- Adding or changing a Project field, a Status value, a view or a built-in workflow.
- Changing a type label, an issue form, the hierarchy guard or the board bridge (`vps-board-operations`).
- Configuring another platform, such as Azure DevOps, from spec §16.
- The start of every agent session, and before execution: run the board bridge's `report` operation (spec §18,
  `vps-board-operations`). It keeps the `scheduling-violation` label on exactly the items it flags.

## Required inputs

- The organization GitHub Project and its current configuration, read with the board bridge's `dump-config`
  operation (`vps-board-operations`).

- `docs/reference/project-automation.md`, which documents the configuration.

## Preflight checks

1. Read spec §11, §14, §15, §17, §18 and §22; for another platform, also §16.
2. The change is an assigned task in an active sprint (`work-sprint-planning-and-eligibility`).

## Actions

1. **Map the specification** as spec §15 describes. Status has seven values (A3). Delivery Stage, Story Points and
   Sprint are Project fields. Releases are milestones. Dependencies are native blocked-by links. Cancellation is
   closed as not planned with Status `Canceled`. Area and Priority are kept; Priority is ordered P0 Critical, P1 High,
   P2 Normal, P3 Later, highest first.
2. **Change single-select options with their option ids** (`updateProjectV2Field` with `singleSelectOptions`
   including each existing `id`), so items keep their values. Without the ids, every item's value is lost.
3. **Keep the views of spec §17** as Project views; a release view gives parent context without assigning parents to
   the release (A2).
4. **Keep the built-in Item closed and Item reopened workflows disabled** (A4). The API can't disable a workflow, so
   ask the owner to do it in the Project's Workflows settings.
5. **Validate in two layers** (spec §22):
   - the `project-hierarchy` workflow, with `GITHUB_TOKEN`: types, parents, milestones, completion, pull request
     chains and mockups;
   - the agent preflight and board report, run by the board bridge with the `pivot-board-bridge` GitHub App: the
     sprint gate, Status against closure reason, a sprint's items sharing its release, estimates, Delivery Stage,
     prerequisites and cycles.
6. **Test a rule with valid and invalid samples** before enforcing it (spec §20), and document every configuration
   change in `docs/reference/project-automation.md`.

## Prohibited actions

- Adding a personal token, or any secret other than the board bridge's App key in the `board` environment, for
  automation (owner decision, spec §22, A11).
- Automation that invents approvals, closes items as Done on a date, or silently reschedules work (spec §18).
- Recreating a single-select field's options without their ids.
- Configuring Azure DevOps outside spec §16, or editing a system process instead of an inherited one.

## Outputs and evidence

- The configuration dump after the change, and the updated reference page.
- The board report's findings, recorded on the task that asked for them.

## Failure behavior

- If the API can't make a change, give the owner the exact UI steps and wait for confirmation.
- If the report finds violations, report them; never fix them by moving dates or sprints.

## Sources

- Spec §11, §14 to §18, §20 and §22 (A2, A3, A4).
- [ADR-0026](../../../docs/adr/0026-adopt-the-work-management-specification.md).
- Owner decisions on AnnabiGihed/RaidManager#323,
  adopted here by [ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md).
