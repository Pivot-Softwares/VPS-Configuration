---
name: work-sprint-review-and-carryover
description: >-
  Use when a sprint reaches its scheduled end or the owner asks for a sprint review: record the goal achievement,
  completed and unfinished work and velocity, and replan unfinished work explicitly, never by automatic carryover.
---

# Sprint review and carryover

The [Work Management and Delivery Specification](../../../docs/reference/work-management-specification.md) is the
authority; this skill applies it. Recording a sprint's outcome and evidence already obtained is administrative and
allowed after the sprint ends (spec §8).

## Triggers

- The current time reaches a sprint's exclusive end (spec §7, §22).
- The owner asks for a sprint review or for unfinished work to be replanned.

## Required inputs

- The sprint record in `docs/planning/sprints/` and every item whose Sprint is that iteration.
- Each item's closure reason, Status and evidence.

## Preflight checks

1. Read spec §7 (sprints), §9 (Story Points and capacity), §13 (completion) and §14 (planning records).
2. Confirm the sprint has really ended; a sprint is never closed early to tidy the board.

## Actions

1. **Record the outcome** in the sprint record, as separate sections: goal achievement, completed work, unfinished work,
   and replanning decisions (spec §7).
2. **Count completed points** only for stories completed within the sprint, with their original estimates; count no
   points for partial or canceled work (spec §9). List bugs, improvements, spikes and stabilization work separately.
3. **Leave unfinished work open.** Its Status reflects its real state; work underway stays `In Progress`, paused by the
   gate (spec §11).
4. **Replan only explicitly:** unfinished work moves to another sprint only when it is selected there, with the
   selection recorded. Before changing an item's Sprint, add its previous sprint to the assignment history of both
   sprint records (spec §7, §15).
5. Set the sprint record's state to Ended, or Canceled with the owner's reason.

## Prohibited actions

- Carrying unfinished work into the next sprint automatically, or changing its Sprint without recording the history.
- Re-estimating to inflate completed points, or counting canceled work as delivered.
- Executing any remaining work after the sprint's end.

## Outputs and evidence

- The updated sprint record: outcome, completed points, unfinished items and replanning decisions.
- For each replanned item, the selection decision and the preserved sprint history.

## Failure behavior

- If an item's state can't be established, record it as unknown in the sprint record and ask the owner.

## Sources

- Spec §7, §8, §9, §11, §13, §14 and §15.
- [ADR-0026](../../../docs/adr/0026-adopt-the-work-management-specification.md).
- Owner decisions on AnnabiGihed/RaidManager#323,
  adopted here by [ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md).
