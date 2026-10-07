# Repository authorship

Use Gihed Annabi for author and owner attribution in documentation, project metadata and copyright notices. Keep this
spelling consistent in future edits.

## Primary goal

Everything in this repository serves a **delivery template that one action applies to any repository of a GitHub
organization**, with the board, the rules, the checks and full automation (owner decisions of 2026-10-07, epic #37).
Read "Primary goal" in `.agents/skills/vps-conventions/SKILL.md` before any work: it states the automation target,
the decisions taken and what "automated" means (nobody, neither the owner nor the agent, triggers it).

## Skills

Project skills live in `.agents/skills/` and, identically, in `.claude/skills/` (for Claude Code).

- Every change to a skill (add, edit, rename, delete) is applied to both trees in the same commit. Before committing,
  confirm the two trees are identical (`diff -r .agents/skills .claude/skills` prints nothing).
- Start every task with `.agents/skills/vps-conventions/SKILL.md`. It states the repository's scope, which imported
  house rules apply, and the working agreements with the owner.
- For work management (creating, classifying and planning work items, sprints, releases, status and completion),
  follow `docs/reference/work-management-specification.md` through the eight `.agents/skills/work-*/SKILL.md` skills
  (ADR-0001).
- For operating the GitHub Project (the board bridge, field ids, creating and linking items, setting fields, the
  closing order), use `.agents/skills/vps-board-operations/SKILL.md`.
- For delivering a change (branch, pull request, review comments, merge and cleanup), use
  `.agents/skills/vps-github-project-workflow/SKILL.md`. A linked task issue is required before implementation.
- For every choice with a consequence, use `.agents/skills/decision-options/SKILL.md`; for every credential,
  `.agents/skills/credentials-policy/SKILL.md`; for every step the owner runs, `.agents/skills/owner-runbook/SKILL.md`.
- For the server itself, use `vps-hardening`, `container-runtime`, `reverse-proxy-caddy`,
  `github-actions-deployment`, `dns-and-mail` and `monitoring-and-backups`.

## Working agreements (every session, mandatory)

- **No standalone work item, ever.** Epic → Feature → User Story, Improvement, Bug or Spike → Task: every item has
  exactly one type label and, except an epic, a parent of the allowed type.
- **No execution outside an active sprint.** Pass the board bridge's `preflight` before starting or resuming a task.
- **One task, one branch, one draft pull request**, following `vps-github-project-workflow`.
- **Never decide alone.** Give options with a recommendation (`decision-options`) and record the owner's answer on the
  issue it settles.
- **No personal access tokens, ever; flag every other credential** (`credentials-policy`).
- **The agent never signs in to the VPS or any provider console.** The owner runs those steps one at a time
  (`owner-runbook`).
- **Before handover:** the quality gates of `vps-conventions` §7.
- **With every pull request, draft both review comments**, the operator's and the peer's. Never post them, approve,
  mark ready or merge.
- **When told a pull request is merged**, confirm it, clean up its branches, and close its task with evidence before
  anything else.
- **"New session"**: run the session-close routine of `vps-conventions` §10.
- **Report automation honestly:** a step the agent or the owner starts is manual, even when a workflow does the work.
- **When the shell is blocked**, continue with the GitHub tools (`vps-conventions` §9); never wait idle.
