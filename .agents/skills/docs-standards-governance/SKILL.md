---
name: docs-standards-governance
description: FAVV-AFSCA Documentation Standards governance. Covers scope, the 🔴/🟡/🟢 compliance model, how to cite rules in reviews, exceptions and waiver ADRs, the new-repository compliance checklist, migrating existing projects, shared tool configurations, and how to amend the standards. Use when reviewing a pull request for documentation compliance, bootstrapping a repository, handling an exception to a documentation rule, or proposing a change to the standards wiki.
---

# Documentation Standards: Governance and Compliance

Source: Development Standards Wiki → *Documentation Standards*. Rule IDs below match that page. Topic rules live in the sibling skills listed at the end.

## 1. Scope

- 🔴 **R1.** The standards apply to every software project maintained by FAVV-AFSCA engineering, whatever the language, stack or deployment target.
- 🔴 **R2.** "Software project" covers application services, libraries, shared packages, infrastructure-as-code repositories and internal tooling.
- 🟡 **R3.** Proof-of-concept and throwaway spikes are exempt from Mandatory rules only when **all** of these hold: expected lifetime under 30 days, not deployed, not shared with other teams. They SHOULD still have a `README.md`. If any condition is false, the project is in scope.

## 2. Compliance model

| Marker | Keyword | Meaning | What you do |
| --- | --- | --- | --- |
| 🔴 Mandatory | MUST / MUST NOT / FORBIDDEN | PRs that violate it are rejected in review or blocked in CI (**R5**) | Always apply. Never propose a violating change. |
| 🟡 Recommended | SHOULD | Deviation allowed when justified in a PR description, team decision or ADR (**R6**) | Apply by default. Deviate only when the user asks, and write the justification into the PR description. |
| 🟢 Optional | MAY | Endorsed good practice, context-dependent (**R7**) | Apply only when the user asks or the task clearly calls for it. |

Shared principles (P1–P6) explain the rules but are not enforceable on their own: single source of truth, docs live with the code, plain text under version control, automate everything mechanical, engineers own their docs, and anything untested is broken.

## 3. Citing rules

- 🔴 **R8.** Every rule is identified by page name and rule number. In review comments, PR descriptions and ADRs, cite rules in exactly this form: `<Page name> / R<n>`.

| Page name to use in citations | Skill |
| --- | --- |
| `Documentation Standards` | `docs-standards-governance` |
| `Documentation as Code` | `docs-as-code` |
| `README, CHANGELOG, CONTRIBUTING` | `docs-root-files` |
| `Diagrams as Code` | `docs-diagrams-as-code` |
| `API Documentation & OpenAPI` | `docs-api-contracts` |
| `Architecture Decision Records` | `docs-adr` |
| `Documentation Review, Linting, and Publishing` | `docs-quality-gates` |

Review comment format:

```markdown
**Blocking** — `Documentation as Code / R4`: this PR changes the default timeout of the HTTP client but does not update `CHANGELOG.md` or `docs/reference/configuration.md`.
```

Use **Blocking** for 🔴 violations, **Suggestion** for 🟡, and do not comment on 🟢 unless asked.

## 4. Exceptions and waivers

- 🔴 **R4.** Any exception to a Mandatory rule MUST be documented in a project ADR. The team lead reviews it; the architecture guild also reviews it when the exception crosses team boundaries.
- 🔴 **R23.** A Mandatory rule MAY be waived temporarily only via an ADR with status `Accepted` and an explicit `Waiver-expires` date. The ADR MUST contain the waived rule by ID, the justification, the remediation plan, and a compliance target date **no more than six months** after the waiver date.
- 🔴 **R24.** An expired waiver that has not been renewed by a new ADR MUST block the next release of the project.

"We will add the docs later" is not a waiver; it is a violation. Ask for either compliance within the PR or a waiver ADR.

### Waiver ADR template

Create it with the `docs-adr` skill (numbering, location and review rules apply), using this content:

```markdown
# ADR-NNNN: Waive <Page name> / R<n> for <scope>

- Status: Accepted
- Date: <YYYY-MM-DD>
- Deciders: <names or handles>
- Waiver-expires: <YYYY-MM-DD, at most six months after Date>

## Context

<Why the project cannot comply now: business or technical justification.>

## Decision

We waive `<Page name> / R<n>` for <exact scope: folders, components, pipelines> until <Waiver-expires>.

## Remediation plan

<Concrete steps and pace, e.g. "enable markdownlint on new files immediately, migrate one folder per sprint".>
Tracking issue: <link>

## Consequences

**Positive**
- <...>

**Negative**
- <...>
```

When reviewing any PR or preparing a release, list every ADR in `docs/adr/` that has a `Waiver-expires` date. Report any date earlier than today with no superseding renewal ADR as release-blocking (**R24**).

## 5. New repositories

- 🔴 **R15.** New repositories MUST comply with every Mandatory rule from day one.
- 🟡 **R16.** Bootstrap from the organizational template `favv-afsca/template-<stack>`, which already contains conforming root files, the `/docs` skeleton, markdownlint and Vale configuration, and the CI pipeline.
- 🟡 **R17.** Create `docs/adr/0001-<title>.md` at initialization, at minimum recording the choice of stack.

### Compliance checklist

A new repository should pass every item before its first production release. Add this checklist to the bootstrap PR description:

```markdown
## Documentation compliance checklist

Root files
- [ ] README.md with purpose, ownership, status, run instructions, links
- [ ] CHANGELOG.md in Keep a Changelog format
- [ ] LICENSE file (proprietary statement for internal-only code)
- [ ] CONTRIBUTING.md with branching, commits, PR process, local setup

Repository layout
- [ ] /docs folder with Diátaxis structure (tutorials, how-to, reference, explanation)
- [ ] /docs/adr/ with ADR-0001 at minimum
- [ ] /docs/diagrams/ with Context and Container diagrams as code

API surface (if applicable)
- [ ] openapi.yaml (or asyncapi.yaml) committed and validated in CI
- [ ] Human-readable API docs published with each release
- [ ] SDK / library reference generated from code comments

CI and publication
- [ ] markdownlint runs on every PR
- [ ] Vale runs on every PR and fails it on errors (`fail_on_error: true` with `vale-action`)
- [ ] Internal link check runs on every PR
- [ ] OpenAPI spec validated on every PR
- [ ] Docs published automatically on merge to main
- [ ] PR preview URL posted as a comment
```

## 6. Existing projects

- 🟡 **R18.** Projects in active development should reach full Mandatory compliance within **six months** of a rule being published or amended.
- 🟡 **R19.** Projects in maintenance mode (security patches only) are grandfathered against new Mandatory rules, but MUST still comply with the Mandatory rules in force when they were last actively developed.
- 🟡 **R20.** Track migration as a checklist issue in the project tracker. Do not propose a single big-bang refactor PR; propose incremental PRs, one checklist item or folder at a time.

## 7. Shared tool configurations

- 🟡 **R21.** Extend the shared configurations in `favv-afsca/engineering-configs` instead of writing new ones: markdownlint-cli2 config, Vale style and terminology packs, Spectral OpenAPI ruleset, lychee config, and the Azure Pipelines templates for documentation CI.
- 🟡 **R22.** Keep deviations minimal and document each one in the project `README.md` under a `## Tooling deviations` heading, stating the setting changed and why.

## 8. Amending the standards

- 🔴 **R9.** The standards are Docs-as-Code: the wiki source is in Git, and every change goes through a pull request against `favv-afsca/dev-standards-wiki`. Never suggest editing the wiki directly in the browser.
- 🔴 **R10.** An amendment to a Mandatory rule needs approval from at least one architecture guild member **and** one representative of an affected product team.
- 🟡 **R11.** Amendments to Recommended or Optional rules need at least one architecture guild approval.
- 🟡 **R12.** Breaking changes (rule removal, new Mandatory rule, upgrade 🟡→🔴) are announced in the engineering-wide channel before merge, with a comment window of at least five working days.
- 🟡 **R13.** Every amendment gets a CHANGELOG entry in Keep a Changelog format, citing the rule ID and the PR number.
- 🟢 **R14.** The standards are reviewed quarterly or semi-annually for drift and accumulating exceptions.

### Procedure when asked to change a standard

1. Edit the page in the wiki repository following the `docs-standards-wiki-page` skill.
2. Add a CHANGELOG entry under `[Unreleased]`:

   ```markdown
   ### Changed
   - API Documentation & OpenAPI / R1: Mandatory scope narrowed to exclude
     endpoints marked with `x-internal-diagnostic: true`. Rationale: these
     endpoints are ephemeral and not consumed by external clients (#47).
   ```

3. Write the rationale in the PR description.
4. List the required reviewers (R10/R11) and, for breaking changes, the announcement and five-day window (R12) as unchecked items in the PR description. You cannot approve, announce or wait; the author does.

## Related skills

`docs-as-code`, `docs-root-files`, `docs-diagrams-as-code`, `docs-api-contracts`, `docs-adr`, `docs-quality-gates`, `docs-standards-wiki-page`.
