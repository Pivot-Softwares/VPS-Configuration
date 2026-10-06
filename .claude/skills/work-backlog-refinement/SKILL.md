---
name: work-backlog-refinement
description: >-
  Use when refining backlog items: completing contracts, writing outcome criteria, estimating Story Points, timeboxing
  spikes, setting priority, recording dependencies, and deciding whether an item is Ready or stays in Backlog. Also
  covers backfilling the contracts of items that predate the specification.
---

# Backlog refinement

The [Work Management and Delivery Specification](../../../docs/reference/work-management-specification.md) is the
authority; this skill applies it. Refinement is planning (spec §8): it is allowed outside an active sprint unless the
refinement is itself an assigned task's deliverable.

## Triggers

- An item is about to be considered for a sprint or release.
- The owner asks for estimates, priorities, criteria or dependencies.
- An item lacks part of its contract, or the board report lists a missing contract or estimate.

## Required inputs

- The item, its parent and children, and its linked decisions and evidence.
- The platform overview in `docs/explanation/` and the related ADRs, for context.
- The Priority ordering documented by `work-board-configuration-and-validation`.

## Preflight checks

1. Read spec §4 (contracts), §9 (Story Points), §10 (readiness and dependencies) and §20 (A6, A7 for existing
   items).
2. The item's type and parent are valid (`work-classification-and-hierarchy`).

## Actions

1. **Complete the contract** of spec §4 from the item's own text, linked decisions and evidence. Keep the original
   content and history; add sections rather than rewriting. Mark what you can't establish as
   `Unknown: needs clarification` (A7).
2. **Write parent criteria as outcomes** (spec §4), not as "every child is closed".
3. **Estimate every story** with 1, 2, 3, 5, 8 or 13 Story Points (spec §9). Agents estimate (spec §22). Post the
   rationale as a comment: effort, complexity and uncertainty, including verification. Split a story that can't
   finish in one sprint. Give a spike its timebox instead of points.
4. **Set Priority** from the documented ordering, with the reason when it isn't obvious.
5. **Record dependencies** as native blocked-by links and in the contract's Dependencies section. Reject cycles. A
   canceled prerequisite isn't satisfied unless an owner decision says it is no longer required (spec §10).
6. **Decide readiness** with the checklist of spec §10. Set Status `Ready` only when every applicable requirement is
   evidenced. Otherwise keep `Backlog` and comment with what is missing (A6).

## Prohibited actions

- Inventing requirements, criteria, estimates' evidence or owner decisions.
- Re-estimating to inflate completed points, or estimating both a story and its tasks (spec §9).
- Setting `Ready` while any applicable contract section is `Unknown`.
- Treating `Ready` as permission to execute; execution needs an active sprint (`work-sprint-planning-and-eligibility`).

## Outputs and evidence

- The completed contract, the estimate comment, the Priority and the dependency links.
- A status comment: `Ready` with the readiness evidence, or `Backlog` with what is missing.

## Failure behavior

- If a product decision is needed, ask the owner on the item and leave it in `Backlog`.
- If a dependency would create a cycle, don't link it; report the cycle.

## Sources

- Spec §4, §8, §9, §10, §20 (A6, A7) and §22.
- [ADR-0026](../../../docs/adr/0026-adopt-the-work-management-specification.md).
- Owner decisions on AnnabiGihed/RaidManager#323,
  adopted here by [ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md).
