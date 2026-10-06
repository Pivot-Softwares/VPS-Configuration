---
name: work-sprint-planning-and-eligibility
description: >-
  Mandatory before starting or resuming any execution (the active-sprint gate), and whenever a sprint is created or
  work is selected into one: sprint dates and record, capacity forecast, readiness and dependency checks, and matching
  sprint and release assignments.
---

# Sprint planning and eligibility

The [Work Management and Delivery Specification](../../../docs/reference/work-management-specification.md) is the
authority; this skill applies it. No task, story, improvement, bug or spike is executed outside an active sprint, and
the check runs before starting and before resuming work (spec §8).

## Triggers

- Before any execution: code, tests, documentation or skill edits, experiments, analysis or design deliverables.
- Before resuming work after a pause, a new session or a sprint end.
- Planning a new sprint, or selecting or removing work during a sprint.

## Required inputs

- The task to execute, its outcome parent, and their Project fields: Sprint, Status, Delivery Stage, assignee and
  milestone.
- The Sprint field's iterations, read with the board bridge's `dump-config` operation (`vps-board-operations`).

- The sprint record in `docs/planning/sprints/`.

## Preflight checks: the gate

Run the board bridge's `preflight` operation for the task (`vps-board-operations`). It reads the Project with the
`pivot-board-bridge` GitHub App, prints PASS or FAIL for each condition with the correction a failure needs, and
fails when any condition fails. Every condition must pass; record the result on the task when you start or
resume:

1. Valid hierarchy and issue contract (`work-classification-and-hierarchy`, spec §4).
2. An assigned sprint with `start <= now < end` and no cancellation. Boundaries are local midnight in Europe/Brussels;
   the end is the start plus the duration, exclusive (spec §7, §22).
3. The task and its outcome parent are in the same sprint.
4. Their release milestones are consistent (spec §15, A2).
5. The task has an assignee and a Delivery Stage.
6. Every prerequisite is completed with evidence, or in the same sprint and already completed before dependent
   execution starts (spec §10).
7. The item is neither canceled nor already completed.

## Actions: planning a sprint

1. Add the next iteration to the Sprint field (two weeks, spec §22) and write
   `docs/planning/sprints/sprint-NN.md` with every field of spec §14: goal, dates and timezone, state, capacity
   assumptions, selected scope and assignment history.
2. Forecast capacity from completed points of previous sprints, adjusted for availability; until history exists, use
   recorded conservative assumptions. Reserve time for bugs, improvements, spikes and stabilization separately from
   points (spec §9).
3. Select only `Ready` items that pass spec §10. Assign the sprint to each outcome item and each of its tasks.
4. Record same-sprint dependencies with their order and delivery risk.

## Prohibited actions

- Executing, or resuming, with any gate condition failing.
- Changing sprint dates, assigning an arbitrary sprint or moving work to pass the gate (spec §8).
- Selecting an item whose prerequisite is unfinished outside the sprint, or a story without an estimate.
- Extending a sprint to finish its scope (spec §7).

## Outputs and evidence

- The gate result on the task: each condition and its evidence.
- For planning: the iteration, the sprint record and the selected items' Sprint values.

## Failure behavior

- Stop, and report the violated rule and the correction it needs (spec §8). Ask the owner when the correction needs a
  decision, such as selecting the item into a sprint.
- If a field can't be read, report it as unknown and don't claim eligibility (spec §18).

## Sources

- Spec §7, §8, §9, §10, §14, §15 and §22.
- [ADR-0026](../../../docs/adr/0026-adopt-the-work-management-specification.md).
- Owner decisions on AnnabiGihed/RaidManager#323,
  adopted here by [ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md).
