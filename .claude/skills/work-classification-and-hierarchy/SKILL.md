---
name: work-classification-and-hierarchy
description: >-
  Mandatory whenever a work item is created, edited, reclassified, linked or flagged needs-parent, on GitHub or any
  other board: select its type by intent then scope, link exactly one parent of the allowed type, set its release
  milestone by level, and write its contract. Nothing is ever standalone.
---

# Work classification and hierarchy

The [Work Management and Delivery Specification](../../../docs/reference/work-management-specification.md) is the
authority; this skill applies it. Read the sections it cites before acting. A standalone or misclassified item is a
major failure: fix it before any other work.

## Triggers

- Creating any issue or work item, on the GitHub Project or any other board.
- Changing an item's type, parent, milestone or scope.
- The `project-hierarchy` workflow labels an item `needs-parent`, or the board report lists a hierarchy problem.

## Required inputs

- The need, defect, question or objective to record, in the requester's words.
- The existing epics and features: `gh issue list --label type:epic --state all` and
  `gh issue list --label type:feature --state all`.
- Owner decisions already recorded on the related issues.

## Preflight checks

1. Read spec §2 (hierarchy), §3 (classification), §4 (contracts) and §15 (GitHub mapping, including amendment A2).
2. Search for an existing item with the same outcome; reuse it rather than creating a duplicate.
3. Confirm the intended parent exists, is open (or reopened with the owner's agreement) and has the allowed type.

## Actions

1. **Classify by intent, then scope** with the procedure and table of spec §3. Split mixed intents into separately
   verifiable items. If a bug's expected behavior was never agreed, ask the owner before calling it a bug.
2. **Choose the parent** allowed by spec §2. When no feature fits, propose a new feature under the right epic.
   Tooling, documentation and process work belongs under the engineering epic named in `vps-conventions` §5.
3. **Create the issue with its issue form** in `.github/ISSUE_TEMPLATE/` (blank issues are disabled), so it gets
   exactly one `type:` label. Write every section spec §4 requires for its type. Record anything you can't establish
   as `Unknown: needs clarification`.
4. **Link the parent at once**, as a native sub-issue:
   `gh api -X POST repos/Pivot-Softwares/VPS-Configuration/issues/<parent>/sub_issues -F sub_issue_id=<child database id>`
   (`gh api repos/Pivot-Softwares/VPS-Configuration/issues/<child> --jq .id` gives the id).
5. **Record prerequisites separately** from the parent (spec §2), as native blocked-by links:
   `gh api -X POST repos/Pivot-Softwares/VPS-Configuration/issues/<dependent>/dependencies/blocked_by -F issue_id=<prerequisite database id>`.
6. **Set the release milestone by level** (spec §15, A2): a task takes its parent's milestone; a story, improvement,
   bug or spike takes the release it is selected for, or none; a feature or epic takes a milestone only when its
   entire scope belongs to that release.
7. **Add it to the Project** and set Area, Priority and Status `Backlog`. Status `Ready` comes only from
   `work-backlog-refinement`.

## Prohibited actions

- Creating or leaving an item without its type label and parent, even briefly, on any board.
- More than one type label; children under a task; an epic created without the owner's approval.
- Using a parent link to express a dependency, or a dependency link to express a parent.
- Forcing a feature or epic that spans releases into one milestone.
- Inventing requirements, acceptance criteria or owner decisions to complete a contract.

## Outputs and evidence

- The issue number, its type label, its native parent and its blocked-by links.
- A contract with every section of spec §4, unknowns marked as such.
- Project fields Area, Priority and Status set.

## Failure behavior

- If the type or parent can't be determined from the evidence, ask the owner; don't create the item orphaned.
- If GitHub access fails, stop; never record the item in a local note instead.
- If the guard flags `needs-parent`, correct the type, parent or milestone it names before doing anything else.

## Sources

- Spec §2, §3, §4 and §15 (A2); [ADR-0026](../../../docs/adr/0026-adopt-the-work-management-specification.md).
- [ADR-0025](../../../docs/adr/0025-classify-work-items-with-spikes-under-features.md), kept as history.
- Owner decisions on AnnabiGihed/RaidManager#323,
  adopted here by [ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md).
