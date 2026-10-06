---
name: pr-and-branching-standards
description: 'Apply the organization''s mandatory branching, commit, pull request, and changelog standards: GitFlow branch
  model (main/develop/feature/fix/release) with work-item IDs in branch names, Conventional Commits titles and commits, the
  five-section PR description, the author self-review checklist, PR size limits, and the same-PR rule for docs, CHANGELOG,
  diagrams, and API contracts. Use whenever creating a branch, writing commits, opening or updating a pull request, or deciding
  what must ship together in one PR.'
---

Apply this skill whenever a change is being branched, committed, or turned into a pull request. It encodes the organization's *Branching and Team Workflow* and *Pull Request Standards* pages; rule IDs below reference those pages. These are mandatory (🔴) unless marked recommended.

## Branch model (GitFlow)

- Only these branch types exist: `main` (production, protected, tag `vX.Y.Z` on every commit), `develop` (integration, protected, always stable), `feature/WORKITEM-ID-short-desc`, `fix/WORKITEM-ID-short-desc` (from `develop`; from `main` only for hotfixes), `release/vX.Y.Z`. Any other type needs prior Technical Lead approval.
- Every `feature/` and `fix/` branch name carries the originating work-item/ticket identifier in upper case, then a short kebab-case description: `feature/AFSCA-1423-supplier-export`. Never open a branch without a ticket reference.
- Branch from `develop`; **pull requests target `develop`**, never `main` directly (release branches are the only path to `main`). If the repository has no `develop` branch, target the default branch and flag the missing branch model in the PR.
- Keep branches short-lived (target ≤3 working days) and rebased on `develop` before the PR goes ready — merge commits from `develop` into the branch are forbidden.
- Direct pushes to `main`/`develop`, force pushes, and self-merges without external review are forbidden for everyone, including automation and the Technical Lead. Urgency never bypasses review; a force-merge requires an active incident, explicit Technical Lead authorization, and a post-mortem within 48 hours.

## Commits and PR title (Conventional Commits)

- The PR title (which becomes the squash commit) and every commit follow:
  `type(scope): imperative summary (WORKITEM-ID)` — types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`; breaking changes add `!` (`feat(api)!: …`).
- Summary in the imperative mood, under 72 characters, no trailing period. Scope names the domain/module touched.
- Commits are atomic (each compiles and represents one logical step); no "wip"/"fix" noise in the final history.

## PR scope and size

- One PR = exactly one work item and one concern. Never bundle tickets; never mix a feature with opportunistic refactoring of unrelated code.
- Target ≤400 changed lines of production code (excluding generated files). When a delivery would exceed it, prefer splitting or flag the size with a justification under Risks.

## The five-section description

Every PR description contains, in order, each filled substantively or with `none` plus a one-line justification:

1. **What changed** — functional terms, not code terms ("Suppliers can export their dossier as PDF", not "Added PdfExporter class").
2. **Why it changed** — work-item link and the business reason.
3. **How it was tested** — tests added, scenarios verified (including unhappy paths), manual checks.
4. **What to review carefully** — where the author is uncertain, constrained decisions, unusual patterns; file and line-range specific.
5. **Migration or deployment notes** — migrations, config changes, flags, deployment order, rollback — or `none`.

## Same-PR artifacts (nothing ships separately)

A change that modifies observable behavior (public API, endpoints, CLI, configuration, build output) ships **in the same PR** with:

- the documentation update under `/docs` — a "docs follow-up PR" is not accepted;
- a **CHANGELOG entry under `[Unreleased]`** (Keep a Changelog sections: Added/Changed/Deprecated/Removed/Fixed/Security; human-readable, referencing the work item; breaking changes explicitly called out) — or the explicit note `none — no user-visible change`;
- the regenerated/updated **API contract** (`openapi.yaml` or equivalent) when the API surface changed;
- updated **diagrams** when the structure they depict changed;
- the **ADR** (or a link to it) when the change implements a decision worth recording.

## Author self-review checklist

Complete before the PR is ready (include it, checked, in the PR):

```markdown
### Author self-review
- [ ] I read the diff end-to-end after my last commit
- [ ] All public interfaces/methods/classes added or changed carry doc comments
      (purpose, parameters, returns, domain constraints)
- [ ] Every non-obvious business rule has a comment explaining the why
- [ ] All TODOs include author, date, ticket, and description
- [ ] Documentation under /docs updated in this PR (or "none — no observable behavior change")
- [ ] CHANGELOG entry added under [Unreleased] (or "none — no user-visible change")
- [ ] No secret, credential, or PII committed
- [ ] CI is fully green on the latest commit
```

- A PR with red or skipped required checks is never ready — "flaky test" is a reason to fix the test, not to merge.
- During review, respond to every comment (address or explain the decline); `blocking:` comments must be resolved before merge; push review fixes as new commits, not force-pushed amendments.

## Completion criteria

- Branch name carries the work-item ID and correct prefix; PR targets `develop` (or the deviation is flagged).
- PR title and commits are Conventional Commits with the work-item ID.
- All five description sections are present and substantive.
- Docs, CHANGELOG `[Unreleased]`, contract, diagrams, and ADR ship in this same PR wherever applicable.
- The self-review checklist is present and every line is genuinely satisfied.

## Pivot.Framework repository specifics

The framework repository deviates from the service branch model in ways this skill must respect (verify before acting — they may change):

- The default and protected branch is **`master`**; there is no `develop` branch yet. Branch from and target `master`, and flag the missing GitFlow model in the PR (per the rule above) rather than creating `develop` unilaterally.
- **Releases are tags, not release branches:** pushing `vX.Y.Z` runs `.github/workflows/publish.yml`, which rewrites `<Version>` in *every* `.csproj`, packs and pushes all `Pivot.Framework.*` packages to GitHub Packages with one shared version. Never hand-edit `<Version>`; never tag without a matching `CHANGELOG.md` section.
- **SemVer is per framework, not per package:** a breaking change in any package (public signature, DI behaviour, persisted schema such as outbox/event-history columns, wire format of RabbitMQ messages) is a MAJOR bump for all of them, with a migration note under `### Breaking changes`.
- CI (`test.yml`, `sonarqube.yml`) runs on PRs to `master`/`main`/`develop`; both must be green.
- Work-item IDs: use the tracker key of the work item (e.g. `feature/PIVOT-42-preserve-event-ids`).
- Same-PR artifacts additionally include the affected `.claude/skills/pivot-*` skill when a change alters behaviour or API described there, and the README drift table in `pivot-framework` when README is corrected.
