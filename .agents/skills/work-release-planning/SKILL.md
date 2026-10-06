---
name: work-release-planning
description: >-
  Use when a release is created or changed: its goal, acceptance criteria, scope, target date, milestone, release
  record and sprint sequence ending in a stabilization sprint, and every owner decision that changes them.
---

# Release planning

The [Work Management and Delivery Specification](../../../docs/reference/work-management-specification.md) is the
authority; this skill applies it. A release record is planning; writing it as an assigned task's deliverable is
execution and needs an active sprint.

## Triggers

- A new release is planned, or an existing release's goal, criteria, scope, target date or sprint sequence changes.
- Work is selected into, or removed from, a release.
- A release changes state (spec §6).

## Required inputs

- The platform scope (`docs/explanation/`) and the candidate items.
- The owner's decisions on goal, scope and target date, recorded on an issue or the release record.
- The sprint calendar (spec §22) and recent velocity, when it exists.

## Preflight checks

1. Read spec §5 (backlogs), §6 (releases), §12 (stabilization), §14 (planning records) and §15 (milestones, A2).
2. Read the current release record in `docs/planning/releases/`, if any.

## Actions

1. **Write the release record** as `docs/planning/releases/<version>.md`, with every field of spec §14: version, goal,
   criteria, target date, scope decisions, sprint sequence, stabilization plan, readiness evidence, approval and actual
   delivery date. Mark drafts as drafts awaiting owner approval. Add it to `mkdocs.yml` and pass the docs checks.
2. **Mirror it on GitHub** (spec §15): the milestone named after the version, with the target date as its due date
   and a description that links the record.
3. **Plan at least two sprints**, the last one a stabilization sprint (spec §6, §12), unless the owner recorded a
   hotfix exception.
4. **Assign the milestone by level** (A2) to the selected items and their tasks.
5. **Record every change** to scope or target date with the owner's decision and reason, in the record and on the
   affected issue.
6. **Track the state** in the record: Planned, In Progress, Stabilizing, Ready, Released (spec §6).

## Prohibited actions

- Inventing a target date, goal, criteria or scope, or treating a draft as agreed.
- Adding or removing release scope without an owner decision.
- Closing the milestone because its sprints ended or its issues closed (spec §6, §13).
- Forcing a feature or epic that spans releases into the milestone.

## Outputs and evidence

- The release record and the milestone, linked to each other.
- The owner's approval or decision for each agreed element, linked from the record.

## Failure behavior

- If an element needs an owner decision, record it as `Unknown: needs owner decision` and ask; the release stays
  short of `Planned` until goal, initial scope and target date exist.

## Sources

- Spec §5, §6, §12, §14, §15 (A2) and §22.
- [ADR-0026](../../../docs/adr/0026-adopt-the-work-management-specification.md).
- Owner decisions on AnnabiGihed/RaidManager#323,
  adopted here by [ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md).
