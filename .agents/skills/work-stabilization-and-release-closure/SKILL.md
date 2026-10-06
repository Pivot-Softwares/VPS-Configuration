---
name: work-stabilization-and-release-closure
description: >-
  Use for a release's final stabilization sprint and for taking a release to Ready and Released: quality work as
  concrete items, readiness checks, owner approval, publication or deployment with evidence, and closing the release.
---

# Stabilization and release closure

The [Work Management and Delivery Specification](../../../docs/reference/work-management-specification.md) is the
authority; this skill applies it. Publication and deployment need the owner's explicit authorization (spec §13).

## Triggers

- Planning or running a release's final sprint.
- Checking whether a release is Ready, or preparing to publish or deploy it.
- A request to close a release milestone.

## Required inputs

- The release record (`docs/planning/releases/<version>.md`) and its milestone.
- Every item in the release scope, with its closure reason and evidence.
- The repository's quality gates (`vps-conventions` §7).

## Preflight checks

1. Read spec §6 (releases), §12 (stabilization) and §13 (completion and closure).
2. The stabilization sprint is active for any execution (`work-sprint-planning-and-eligibility`).

## Actions

1. **Plan stabilization as concrete items** (spec §12): improvements, bugs or spikes with child tasks and acceptance
   criteria, for blocking defects, regressions, identified refactoring and cleanup, end-to-end validation,
   documentation, release notes, deployment and rollback preparation. Avoid new features.
2. **Keep failed checks as unresolved work**; never waive them by closing the item.
3. **Check readiness:** the release's acceptance criteria and checks pass; record the evidence in the release record
   and set its state to Ready.
4. **Ask the owner for approval** to publish or deploy, and record the approval.
5. **Publish or deploy** only after approval, then record the evidence and the actual delivery date, and set the
   state to Released. The evidence includes the `Deployed to production` line the deployment adds to the release
   milestone's description, once every item carries `deployed:production` (spec §22, A9).
6. **Close the milestone** only after the delivery evidence is recorded (spec §6).
7. If necessary work remains when stabilization ends, ask the owner to revise the scope, the date or the next sprints
   (spec §12).

## Prohibited actions

- Treating the end of stabilization, or of any sprint, as release authorization.
- Publishing, deploying or tagging without the owner's recorded approval.
- Closing the milestone without delivery evidence, or removing scope without an owner decision.

## Outputs and evidence

- Stabilization items with evidence; the release record with readiness evidence, approval, delivery evidence and
  date; the closed milestone.

## Failure behavior

- If a check fails or evidence is missing, the release stays short of Ready; report what is missing and ask the owner
  how to replan.

## Sources

- Spec §6, §12 and §13.
- [ADR-0026](../../../docs/adr/0026-adopt-the-work-management-specification.md).
- Owner decisions on AnnabiGihed/RaidManager#323,
  adopted here by [ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md).
