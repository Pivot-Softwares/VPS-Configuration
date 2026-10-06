---
name: repository-readiness
description: 'Check that a repository is configured for a coding agent (Claude Code or Copilot) before doing real work, and fail fast with an actionable fix when it is not. Defines the readiness preconditions for services built on Pivot.Framework (skills kit, build props, nuget.config with the Pivot GitHub Packages feed, package read token, firewall allowlist, Pivot source access, local Keycloak/RabbitMQ/database via Aspire), which the agent can self-repair versus which need a human, how to judge relevance to the task, and the exact analyst-voice user story to emit. Use at the very start of every task, before planning or writing code.'
---

Run this check **first, before planning or editing anything**. It prevents half-done tasks on a misconfigured
repository and broken or fallback results. Principle: **fail fast with an actionable fix, never degrade silently.**

## The readiness gate

1. **Detect** which preconditions below are satisfied.
2. **Classify** each unmet one as *agent-fixable* or *human-only*.
3. **Judge relevance** — does the current work item depend on it? (A Markdown-only task doesn't need NuGet restore.)
4. **Act:**
   - Unmet, task-relevant, **human-only** → don't attempt the parts that will fail. Deliver only what is safe and independent, make the readiness report the PR headline, and emit the setup user story. Never produce a fallback, substitute or vendored workaround (no copying Pivot source into the repo, no hand-rolled lookalikes of Pivot base types, no local `.nupkg` checked in).
   - Unmet, task-relevant, **agent-fixable** → fix it in this PR and note it.
   - Unmet, not relevant → note under Risks and continue.
5. **Ready** → do the task; one line "readiness: OK" in the PR.

If `readiness: strict` is set in `CLAUDE.md` or `.github/copilot-instructions.md`, treat any unmet precondition as blocking.

## Precondition catalog

| Precondition | Detect | Fixer | Gates |
|---|---|---|---|
| **Skills kit installed** | `.agents/skills/` in RaidManager (elsewhere `.claude/skills/` or `.github/skills/`) with the `pivot-*` and house skills | Human (sync) | Convention fidelity on everything |
| **Repository instructions** | `CLAUDE.md` / `.github/copilot-instructions.md` exists | Human (sync) or agent | House rules |
| **Build props** | `Directory.Build.props` (net10.0, nullable, analyzers, doc generation) + `Directory.Packages.props` (CPM, Pivot packages pinned together) | Agent | Any .NET build |
| **NuGet config** | `nuget.config` declares `https://nuget.pkg.github.com/AnnabiGihed/index.json` with package source mapping `Pivot.Framework.*` → that feed and `%PIVOT_PACKAGES_USER%`/`%PIVOT_PACKAGES_TOKEN%` credentials — no committed token | Agent | Pivot restore |
| **Package read access** | env/secret `PIVOT_PACKAGES_TOKEN` (GitHub PAT, `read:packages`) + `PIVOT_PACKAGES_USER` available to the agent | Human | Restore — `401` if missing |
| **Registry allowlisted** | `nuget.pkg.github.com` (and `api.nuget.org`) reachable from the agent sandbox/firewall | Human | Restore — DNS/timeout if blocked |
| **Pivot source access** | agent can read `github.com/AnnabiGihed/Pivot.Framework` (checkout, MCP GitHub server, or the `pivot-*` skills present) | Human | Verifying signatures instead of guessing |
| **Local dependencies** | Aspire AppHost orchestrates the database (SQL Server/PostgreSQL), RabbitMQ, Redis (if used) and a **Keycloak** container with a realm import | Agent (add AppHost resources + realm JSON) | Running/E2E-testing auth, messaging, persistence |
| **Keycloak client config** | realm/client ids and an audience mapper present in the realm import; `Keycloak` section in `appsettings.Development.json` (no secrets) | Agent | Authentication work only |
| **Docker available** | `docker info` succeeds in the agent environment | Human | Testcontainers E2E tests, Aspire run |

The agent can't read secrets or firewall settings directly — infer from behaviour: `401 Unauthorized` from GitHub Packages ⇒ missing/invalid token or token lacks `read:packages`; `NU1101 Unable to find package Pivot.Framework.*` with credentials present ⇒ wrong feed URL or missing source mapping; DNS failure/timeout ⇒ host not allowlisted; `404` reading the Pivot repository ⇒ no source access. When you can't verify, list them as "unverified prerequisites" in the story rather than asserting they are wrong.

## Agent-fixable vs human-only

- **Self-repair in the PR** (then note it): `Directory.Build.props`, `Directory.Packages.props`, `nuget.config`, `.editorconfig`/`stylecop.json`, `.gitignore`, AppHost resources and the Keycloak realm import, a minimal `CLAUDE.md` if wholly absent. Follow `dotnet-solution-scaffolding` and `clean-code-static-analysis`.
- **Human-only — emit the story, never work around:** creating/storing the package-read token, allowlisting hosts, granting source access, installing Docker/Aspire workload on the agent image, syncing the skills kit.

## The setup user story

When a human-only precondition blocks the task, end the readiness report with this ready-to-paste story, listing only the missing items:

```markdown
## USER STORY — Make <repo> ready for the coding agent

**Expected outcome**
The repository is configured so the coding agent can restore, build and run tasks that depend on the
Pivot.Framework packages (and, where relevant, Keycloak, RabbitMQ and the database) without falling back or failing.

**Why**
Work item <ID> could not be completed: <one line naming the blocked precondition(s)>. The agent delivered
<what it did / nothing> and stopped rather than shipping a workaround.

**Setup checklist** (each item done by a human with the stated rights)
- [ ] Create a GitHub PAT (classic, `read:packages`) from a service account with access to the AnnabiGihed packages, and expose it to the agent as `PIVOT_PACKAGES_TOKEN`, with `PIVOT_PACKAGES_USER` set to the account name. A `401` on `nuget.pkg.github.com` means this is missing.
- [ ] Allow outbound access from the agent environment to `nuget.pkg.github.com` and `api.nuget.org`.
- [ ] Give the agent read access to `AnnabiGihed/Pivot.Framework` (checkout or GitHub MCP token with Contents: Read).
- [ ] Sync the skills kit (`pivot-*` + house skills) into `.agents/skills/` (RaidManager) or `.claude/skills/` / `.github/skills/` and merge it to the default branch.
- [ ] Make Docker and the Aspire workload available on the agent image (only for tasks that run the app or E2E tests).

**Acceptance criteria**
- `dotnet restore` resolves every `Pivot.Framework.*` package from GitHub Packages; build green; no fallback, no vendored packages or copied framework source.
- (If auth/messaging is in scope) the AppHost starts Keycloak, RabbitMQ and the database, and the E2E suite authenticates against Keycloak.

**Out of scope**
- Any application feature — this story only makes the repository workable by the agent.
```

## Completion criteria
- Readiness checked before any planning or edits; each unmet precondition classified and judged against the task.
- Agent-fixable, task-relevant gaps repaired in the PR; human-only blockers stopped dependent work instead of a fallback.
- When blocked, the PR headline is the readiness report ending with the tailored story; a ready repo gets "readiness: OK".
