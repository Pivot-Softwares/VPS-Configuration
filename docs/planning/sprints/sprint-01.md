# Sprint 1

The planning record of Sprint 1, kept as the [Work Management and Delivery
Specification](../../reference/work-management-specification.md) requires (§7, §14).

| Field | Value |
| --- | --- |
| Sprint | Sprint 1 (Project iteration `Sprint 1`) |
| State | Active |
| Start | 2026-10-06 00:00 Europe/Brussels, inclusive |
| End | 2026-10-20 00:00 Europe/Brussels, exclusive |
| Duration | Two weeks (specification §22) |
| Release | [`v1.0`](../releases/v1.0.md), its first delivery sprint |

The owner chose these dates on 2026-10-06, as the recommended option, so planned work can start at once.

## Sprint Goal

Put the board foundation in place (the board bridge, the issue forms, the type and rule labels, the hierarchy guard),
then agree the plan for the VPS's security and the three deployments as decision records and work items.

## Capacity assumptions

20 Story Points, the owner's decision of 2026-10-06 (recorded on #5): conservative, since this repository has no
velocity yet (specification §9). Selected: 18 points.

## Selected scope

The board foundation (#1, #2) was delivered without work items by the owner's bootstrap decision (ADR-0001). The
owner selected these items on 2026-10-06 (recorded on #5). Each planned window is the sprint (2026-10-06 to
2026-10-19, both inclusive on the Project).

| Item | Type | Story Points | Tasks (Delivery Stage) | Waits for |
| --- | --- | --- | --- | --- |
| #21 The board bridge and the sprint gate read no Project items | Bug | 2 | #22 (Development) | None |
| #5 Plan release v1.0 and Sprint 1 in the repository | Improvement | 2 | #6 (Business Analysis) | None |
| #7 Let the board bridge manage sprints and field options | Improvement | 3 | #8 (Development) | #6 for the gate |
| #24 Keep native issue types in step with the type labels | Improvement | 3 | #25 (Development) | #6 |
| #29 Done doesn't close items and new issues aren't added to the Project | Bug | 3 | #30 (Development) | None |
| #31 Port RaidManager's review gate, merge and pull-request checks | Improvement | 5 | #32, #33, #34 (Development) | #32 before #33, #33 before #34 |

Bug #21 and task #22 started on 2026-10-06 under a recorded exception to the gate (standing owner decision on #21:
blocking board bugs come first), and #6 under a one-time exception for condition 4, since the release record is its
own deliverable (owner decision on #6). The bug was completed on 2026-10-06 by the merge of #23.

## Assignment history

| Date | Change | Recorded on |
| --- | --- | --- |
| 2026-10-06 | #5, #6, #7, #8, #21 and #22 selected. | #5 |
| 2026-10-06 | #24 and #25 added. | #5 |
| 2026-10-06 | #29 to #34 added, all P0 Critical: full automation and a correct board come first (owner's option 1). | #29, #31 |

## Outcome

Recorded when the sprint ends (specification §7).
