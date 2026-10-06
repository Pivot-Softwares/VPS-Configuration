---
name: vps-conventions
description: >-
  VPS-Configuration precedence rules over the imported house skills, and the working agreements with the owner. Use at
  the start of every task in this repository, and whenever another skill mentions Keycloak, Pivot.Framework, .NET,
  FAVV-AFSCA, Azure DevOps, GitFlow, a personal token or a local `gh` login: it states which of those rules apply here,
  which are replaced, and which questions must be asked instead of decided.
---

# VPS-Configuration conventions and skill precedence

This repository configures, secures and documents the shared OVH VPS (2 vCores, 4 GB memory, 40 GB storage) that hosts
the Pivot Softwares applications under `pivotsoftwares.com`. Owner and author: Gihed Annabi (`@AnnabiGihed`). It follows
the RaidManager work process exactly ([ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md)).
Precedence, highest first:

1. Accepted ADRs in `docs/adr/`.
2. Configuration enforced by tooling in this repository: `.github/workflows/*.yml`, lint configurations.
3. This skill and the other `vps-*` skills, `credentials-policy`, `decision-options` and `owner-runbook`.
4. The `work-*` skills, which apply the
   [Work Management and Delivery Specification](../../../docs/reference/work-management-specification.md).
5. The imported house skills (`docs-*`, `pr-and-branching-standards`, `repository-readiness`,
   `architecture-proposal`).

## 1. Scope of this repository (owner decision B, ADR-0001)

- **This repository owns everything shared on the server:** operating-system hardening, SSH, firewall, users,
  automatic updates, the container runtime, the reverse proxy and its certificates, monitoring, alerting, backups,
  the deploy accounts and the DNS records the owner enters by hand.
- **Each application repository owns only its own deployment** into the slot this repository gives it:
  `AnnabiGihed/RaidManager` (dev, test and production), `AnnabiGihed/Delivery-Atlas` and
  `AnnabiGihed/PivotSoftwarsWebsite` (production only). Changes there are pull requests only; never push to them.
- RaidManager's own server files (`deploy/server/provision.sh`, its Caddyfile, ADR-0027 and ADR-0028) move here
  through pull requests in both repositories, linked to each other.
- The server is reset from scratch; nothing is backed up from the old installation and Azure DevOps isn't used
  (owner decisions, ADR-0001).

## 2. Imported skills: what applies here

| Imported skill says | VPS-Configuration uses |
| --- | --- |
| GitFlow, `develop`, `release/` branches (`pr-and-branching-standards`) | `main` only. `feature/<task>-<slug>` or `fix/<task>-<slug>` from `origin/main`; pull requests target `main`; squash merges. The commit, title, five-section description and self-review rules apply. |
| Work-item id in upper case (`AFSCA-1423`) | The GitHub issue number of the **task** (`feature/12-ssh-hardening`, `(#12)` in commit titles). |
| Azure DevOps pipelines and wiki, `::: mermaid` | GitHub Actions; fenced `mermaid` blocks; documentation published from `docs/` once its publishing is decided. |
| Keep Mermaid to the Azure DevOps subset (`docs-diagrams-as-code`) | Still keep to that subset: it renders everywhere. |
| .NET build props, analyzers, Pivot feed, Keycloak, Aspire (`repository-readiness`, `architecture-proposal`) | Not applicable: there is no .NET code here. The readiness gate still runs, with the preconditions of §6. |
| The Pivot.Framework mandatory frame (`architecture-proposal`) | Not applicable. The document structure, argued decisions, Proposed ADRs and C4-as-flowchart diagrams apply to the platform architecture. |
| FAVV-AFSCA standards wiki, guilds, technical writers, `favv-afsca/*` repositories (`docs-standards-*`) | None exist. Severity markers and rule citations still apply; the owner is the reviewer; never invent contacts or URLs. |
| `PIVOT_PACKAGES_TOKEN` or any personal token | Forbidden (`credentials-policy`). |
| Skills under `.claude/skills/` only | `.agents/skills/` and an identical `.claude/skills/`, changed together in one commit (`AGENTS.md`). |

## 3. People and accounts

- **Operator:** the owner, `@AnnabiGihed`. Reviews first, marks a pull request ready, takes every decision.
- **Peer reviewer:** `@anthermook`, who approves after the operator. They need write access to the repository.
- **The agent** works from Claude Code cloud sessions: no local `gh` login, no access to the owner's PC or the VPS.

## 4. Open owner questions (ask, never decide)

| Question | State |
| --- | --- |
| Repository visibility: public (recommended) or private on the Free organization plan, which loses branch protection, Pages and wiki | Open |
| Sprint 1 dates | Settled: 2026-10-06 to 2026-10-20 (ADR-0001) |
| The first release: goal, scope and target date | Open |
| Every technical choice the plan contains (operating system, reverse proxy, monitoring, backups, deployment method) | Each one is a decision record with options (`decision-options`) |

When one of these is settled, record the decision (§8) and update this table in the same pull request.

## 5. Work management (mandatory)

The specification is the authority; the eight `work-*` skills apply it, `vps-board-operations` holds the commands
and `vps-github-project-workflow` the branch, pull request and review mechanics. These override the ticket rules of
`pr-and-branching-standards`:

- Nothing is standalone: Epic → Feature → User Story, Improvement, Bug or Spike → Task (spec §2). Breaking this is a
  major failure.
- No task, story, improvement, bug or spike is executed outside an active sprint (spec §8).
- A branch, commit and pull request always carry a **task** number.
- Tooling, documentation and process work belongs under the epic **Engineering platform and delivery** once the owner
  approves creating it. Never create an epic without the owner's approval.
- **Bootstrap exception (owner decision E, ADR-0001):** the first version of the skills and the board foundation were
  delivered without work items. Every later change needs its work item.
- **Board bugs come first (standing owner decision on #21, 2026-10-06):** a bug in the board, the board bridge, the
  guard or the gate has Priority P0 Critical. When it blocks work, including the gate itself, its task starts under a
  **recorded exception**: check the gate's seven conditions by hand from the issue data and the last field writes,
  post the table on the task (as on #22), then go back to the real gate once the bug is fixed.

## 6. Readiness preconditions for this repository

Run `repository-readiness` with these preconditions instead of the .NET ones:

| Precondition | Detect | Fixer |
| --- | --- | --- |
| Skills installed | `.agents/skills/` and `.claude/skills/` identical | Agent |
| Board bridge | The `board` workflow exists on `main` and its last run succeeded | Agent (pull request) and owner (App and environment) |
| Organization Project | The Project URL and number are recorded in `vps-board-operations` | Owner |
| Repository access | The cloud session has `Pivot-Softwares/VPS-Configuration` attached | Owner (Claude GitHub App on the organization) |
| Application repositories | The application repository a task changes is attached to the session | Owner |

## 7. Quality gates before handover (mandatory)

Until the repository's own checks exist, run them locally on every changed file and quote the results:

- **Markdown:** `markdownlint-cli2` with the configuration in `.markdownlint-cli2.yaml` once it exists (line length
  120, skills excluded, as in RaidManager).
- **Shell:** `shellcheck` on every script; `bash -n` at least.
- **Workflows:** `actionlint` on every changed workflow; third-party actions pinned to a full commit id with the version
  in a comment.
- **YAML:** `yamllint` on every changed YAML file.
- **Secrets:** a secret scanner (`gitleaks detect --no-git` on the changed files) before every push. A finding is
  never pushed, even in a draft.
- **Skills:** `diff -r .agents/skills .claude/skills` prints nothing.

When a check can't run in the session, say so in "How it was tested"; never report it as passed.

## 8. Working with the owner (mandatory)

Carried over from RaidManager (`raidmanager-conventions` §13) and the owner's instructions for this repository.

- **Never decide alone.** Every choice with a security, cost, architecture, tooling or process consequence is
  presented with `decision-options`: two to four options, the recommended one first and marked "(Recommended)",
  each with its pros, cons and consequence. Wording and file names inside the agreed structure are the agent's call
  and stay visible in the pull request (owner decision on question 14, ADR-0001).
- **Record every owner decision on the issue it settles**, under `### Owner decisions (<date>, recorded here)` or as a
  comment, before acting on it. Decisions that shape the platform also become ADRs.
- **Flag every credential.** Any token, key or password the plan needs is marked ⚠️ and justified with
  `credentials-policy`. Personal access tokens are forbidden.
- **The agent never signs in to the VPS, the OVH Control Panel, name.com, Zoho or GitHub settings.** The owner runs
  those steps. Give owner steps with `owner-runbook`: one at a time, what, where, why, what to expect.
- **Never ask for or handle credentials.** Ask for facts (versions, names, outputs) without secrets.
- **Learn the server's state from read-only commands** the owner runs and pastes, and from outside checks (DNS, HTTPS,
  certificates, SSH methods, open ports). Record both on the issue.
- **Automation first.** Prefer a change delivered by a workflow over a manual step on the server; a manual step needs a
  reason in the runbook.
- **"Merged"** means: confirm the merge with the GitHub tools, clean up the branches, close the task and its validated
  parents with evidence, run the board report, then report and propose the next item.
- **Report like this:** lead with the result; then what changed on the board and in the files, the checks run with
  their results, what to review carefully, and the two drafted review comments verbatim. Name your own mistakes
  plainly. Keep it short.
- **Dates and times** are absolute and in Europe/Brussels.

## 9. Cloud session mechanics

- GitHub GraphQL and user-level APIs are blocked in cloud sessions. Repository-scoped REST calls (`gh api
  repos/Pivot-Softwares/VPS-Configuration/...`) and the GitHub MCP tools work. Project fields are read and written only
  through the board bridge (`vps-board-operations`).
- A repository is attached with `add_repo` and cloned under `/home/user/<name>`. Two repositories with the same name
  can't share a session.
- Write files with LF line endings. The owner's PC is Windows: owner steps on the PC use PowerShell.

## 10. Ending a session ("new session", mandatory)

When the owner says "new session", without asking for details again:

1. **Checkpoint:** finish or push the work in progress and record its state on its task.
2. **Lessons:** create an improvement under the engineering feature with one task, selected into the active sprint,
   that records the session's lessons in the skill that owns each topic (both trees), and one pull request for it.
3. **Handover message** in one fenced `text` block: the skills to read first, open pull requests and what to do when
   each merges, Blocked items with their unblock condition, the sprint and release, and the first action of the next
   session.

## Sources

- [ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md) and the owner decisions it records.
- `AnnabiGihed/RaidManager`: `AGENTS.md`, `raidmanager-conventions`, `docs/reference/project-automation.md`.
