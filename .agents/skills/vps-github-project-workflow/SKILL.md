---
name: vps-github-project-workflow
description: >-
  Mandatory repository mechanics for every VPS-Configuration change: one task, one branch, one draft pull request, the
  pull request description and checks, the two review comments, merging and branch cleanup, and pull requests to the
  application repositories. Work-management policy (hierarchy, classification, sprints, the active-sprint gate, status,
  completion, releases) is in the work-* skills and the Work Management and Delivery Specification.
---

# VPS-Configuration GitHub Project workflow

Use this skill whenever you deliver any change: server configuration, workflows, scripts, documentation, decision
records or skills. Read `../vps-conventions/SKILL.md` first. It mirrors `raidmanager-github-project-workflow`; its
`main`-only branch model overrides the GitFlow rules of `pr-and-branching-standards`, whose commit and pull request
quality rules apply.

The [Work Management and Delivery Specification](../../../docs/reference/work-management-specification.md) is the
authority (ADR-0001), applied by eight skills:

| Skill | Use it for |
| --- | --- |
| `work-classification-and-hierarchy` | Creating, classifying and linking any work item; nothing is standalone. |
| `work-backlog-refinement` | Contracts, criteria, Story Points, priority, dependencies, Ready or Backlog. |
| `work-release-planning` | Release goal, scope, target date, milestone, record and sprint sequence. |
| `work-sprint-planning-and-eligibility` | Sprints, capacity, selection, and the active-sprint gate before any execution. |
| `work-task-execution-and-completion` | Status and Delivery Stage while working, completion, cancellation, reopening. |
| `work-sprint-review-and-carryover` | Sprint outcomes and explicit replanning of unfinished work. |
| `work-stabilization-and-release-closure` | Stabilization, readiness, approval, delivery and release closure. |
| `work-board-configuration-and-validation` | Project fields, views, workflows, forms, the guard and the board report. |

The commands are in `vps-board-operations`.

## Source of truth

- Repository: `Pivot-Softwares/VPS-Configuration`; the organization Project recorded in `vps-board-operations`.
- Releases are repository milestones with release records in `docs/planning/releases/`.
- Work items use `type:` labels and native parent/sub-issue and blocked-by links, created with the issue forms in
  `.github/ISSUE_TEMPLATE/`.

## Mandatory delivery sequence

1. Find the task that carries the change, or create it with `work-classification-and-hierarchy`. Never create a
   duplicate to gain a new branch. If GitHub access fails, stop before implementation.
2. Pass the active-sprint gate (`preflight`) before starting and before resuming. If it fails, stop and report the
   violated rule.
3. Fetch the latest `main` and create one `feature/<task-number>-<slug>` or `fix/<task-number>-<slug>` branch from
   `origin/main`. Documentation, decision records, planning and skills use `feature/` too. No other prefix, no
   `develop`, no direct push to `main`. Set Status and Delivery Stage (`work-task-execution-and-completion`).
4. Implement only the task's scope while satisfying the parent's applicable criteria:
   - every choice with a consequence goes through `decision-options` before it is implemented;
   - every credential is flagged with `credentials-policy`;
   - every step on the server, OVH, name.com, Zoho or GitHub settings is written with `owner-runbook`;
   - run the quality gates of `vps-conventions` §7 and record the results;
   - edit both skill trees identically.

   Update the affected documentation, decision records, diagrams and changelog in the same change. Record a justified
   `none` for an artifact that genuinely does not apply.
5. Review the final diff, stage only the files the task changed (never `git add -A` or `git add .`), commit with a
   Conventional Commit title containing the task number, push, and open one **draft** pull request against `main`:
   - `Closes #<task-number>` on a standalone line before the first heading. Only tasks are closed by a pull request;
     reference parents with `Refs #<number>`. No closing keyword anywhere else.
   - The five sections in this order: `## What changed`, `## Why it changed`, `## How it was tested`,
     `## What to review carefully`, `## Migration or deployment notes` (`None.` if none), then `### Author
     self-review` with the checklist of `pr-and-branching-standards`. Never describe a skipped or failing check as
     passed.
   - A **Credentials** line: `None.` or each credential the change introduces or touches, flagged ⚠️.
   - When the change needs steps on the server or a provider console, say whether they run before or after the merge.
6. Never mark the pull request ready, approve it, merge it, or write a review in the operator's name (RaidManager
   ADR-0006, ADR-0009). Tell the operator the draft is ready once its checks are green.
   - **Check first, review texts after.** When the task's completion needs an owner check (a run on the server, a
     provider setting), give the check steps one at a time first and the review texts only after the check passed.
   - **Check every fact the description states** in the files or the run before opening the pull request.
   - **Draft both review comments, every pull request (mandatory):**
     1. the **operator's review comment**, about intent: what the operator checked and why it is what they decided;
     2. the **peer's approval comment** (`@anthermook`), about the files: what was reviewed and what it guarantees.

     Each names something the pull request changes (a file or an identifier), has at least ten meaningful words and
     no generic praise, and the two are not copies of each other. The shape that works: `Operator review of #<pr>. I
     checked ...` (or `Peer review of #<pr>. I compared ...`), then four bullets, each naming a file or identifier and
     what was verified about it.
   - **One pull request at a time, or a stated merge order.** Bring a branch up to date by merging `origin/main` into
     it, never by rebasing and force-pushing.
   - Until the `review` workflow is ported from RaidManager, the operator merges with **Squash and merge** after the
     peer's approval; never merge yourself.
7. After the merge, close out with `vps-board-operations` ("Close after a merge"). Branch cleanup is mandatory before
   any other work: confirm the merge, delete the remote branch if it remains, and delete the local branch.

## Pull requests to the application repositories

The owner allows pull requests, never direct pushes, to `AnnabiGihed/RaidManager`, `AnnabiGihed/Delivery-Atlas`,
`AnnabiGihed/PivotSoftwarsWebsite` and `AnnabiGihed/Pivot.Framework`.

- The work item lives here (the platform side) and links the application's own item when it has one.
- Follow the target repository's own `AGENTS.md`, conventions and pull request rules; RaidManager's apply in full
  there, including its own task, sprint gate and review gates.
- Name the target repository in every issue reference (`AnnabiGihed/RaidManager#123`).

## Sources

- `AnnabiGihed/RaidManager`: `raidmanager-github-project-workflow`, `CONTRIBUTING.md`, ADR-0004 to ADR-0009.
- [ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md).
