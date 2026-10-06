---
name: docs-root-files
description: FAVV-AFSCA rules and templates for repository root files README.md, CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, LICENSE and optional SECURITY.md, SUPPORT.md, MAINTAINERS.md. Use when creating a repository, writing or reviewing any of these files, adding a changelog entry, or preparing a release.
---

# Root Documentation Files

Source: Development Standards Wiki → *README, CHANGELOG, CONTRIBUTING*. Cite rules as `README, CHANGELOG, CONTRIBUTING / R<n>`. Severity handling follows `docs-standards-governance`.

Never invent facts to fill these files (team names, channels, URLs, pipeline links, security contacts). Take them from the repository or the user; if unknown, ask.

## 1. README.md

- 🔴 **R1.** `README.md` exists at the repository root.
- 🔴 **R2.** Within the first screen it answers, in this order:
  1. **What** the project is, in one sentence.
  2. **Status**: exactly one of `Production`, `Beta`, `Experimental`, `Deprecated`.
  3. **Who** owns it: team name and contact channel.
  4. **How to run it locally**: copy-pasteable commands.
  5. **Where the full documentation is**: a link.
- 🟡 **R3.** Build, coverage and version badges when available.
- 🟡 **R4.** At most ~150 lines. It is a launch pad; move detail into `/docs`.
- 🔴 **R5.** "See the wiki" MUST NOT be the only pointer to documentation.
- 🟡 **R6.** Links to `CONTRIBUTING.md`, `CHANGELOG.md`, the published docs site, the issue tracker and the deployment pipeline.
- 🟢 **R7.** A "Screenshots" or "Demo" section for user-facing products.
- Tooling deviations from shared configs are listed under `## Tooling deviations` (`Documentation Standards / R22`).

### Template

````markdown
# <repository-name>

<One sentence: what it does, for whom, main technologies.>

<badges>

## Status

**<Production | Beta | Experimental | Deprecated>.** Owned by <Team name> (<contact channel>).

## Run locally

Prerequisites: <.NET SDK version, Docker, ...>

```bash
<command 1>
<command 2>
```

<Where the running app is reachable, e.g. https://localhost:5001>

## Documentation

- **Docs site**: <url>
- **API reference**: <url or ./docs/reference/api.md>
- **Architecture**: [docs/explanation/](./docs/explanation/)
- **Decisions**: [docs/adr/](./docs/adr/)
- **Changelog**: [CHANGELOG.md](./CHANGELOG.md)
- **Issues**: <tracker url>
- **Pipeline**: <pipeline url>

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

Proprietary. See [LICENSE](./LICENSE).
````

## 2. CHANGELOG.md

- 🔴 **R8.** Required for every repository producing a released artifact (library, service, CLI, container image).
- 🔴 **R9.** [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format with sections `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- 🔴 **R10.** [Semantic Versioning 2.0.0](https://semver.org/): `MAJOR.MINOR.PATCH`.
- 🔴 **R11.** Each release has its own heading with an ISO 8601 date: `## [2.4.0] - 2025-11-14`.
- 🔴 **R12.** Breaking changes go under `### Breaking changes` and force a MAJOR bump.
- 🟡 **R13.** Written for humans. A list of commit messages is not a changelog.
- 🟡 **R14.** Each entry references its PR or issue number: `(#512)`.
- 🟡 **R15.** Keep an `## [Unreleased]` section at the top.

### Adding an entry

1. Add it under `## [Unreleased]`, never under an already released version.
2. Pick the section by the effect on the consumer:

| Effect | Section |
| --- | --- |
| New capability | `### Added` |
| Existing behavior changes compatibly | `### Changed` |
| Still works, scheduled for removal | `### Deprecated` |
| Capability removed | `### Removed` (also `### Breaking changes`) |
| Bug fix | `### Fixed` |
| Vulnerability or dependency CVE fix | `### Security` |
| Consumer must change their code or config | `### Breaking changes`, with a migration link |

3. Write one sentence in the past or present tense describing the effect for the consumer, name the endpoint, type or setting in backticks, and end with the reference: `- \`POST /payments\` now requires the \`Idempotency-Key\` header (#513).`
4. Do not create empty sections.

### Cutting a release

Rename `## [Unreleased]` content into `## [X.Y.Z] - YYYY-MM-DD`, choose X.Y.Z by semver (any breaking change → MAJOR, any Added → MINOR, otherwise PATCH), and add a fresh empty `## [Unreleased]` above it.

### Template

```markdown
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Support for partial refunds via `POST /payments/{id}/refunds` (#512).

## [2.4.0] - 2025-11-14

### Added
- `Idempotency-Key` header is now required on `POST /payments` (#513).

### Fixed
- Fixed a race condition when two refunds were issued simultaneously (#495).

### Breaking changes
- `POST /payments` returns `400` if `Idempotency-Key` is missing. Previously
  the header was optional. Migration guide: [docs/migration/v2.4.md](./docs/migration/v2.4.md).
```

## 3. CONTRIBUTING.md

- 🔴 **R16.** Required in every repository accepting external or cross-team contributions.
- 🔴 **R17.** Documents all of:
  - branching strategy;
  - commit message convention (Conventional Commits by default);
  - PR process: required reviewers, required checks, merge strategy;
  - local development setup: prerequisites, build, test;
  - how to report a security vulnerability, or a link to `SECURITY.md`.
- 🟡 **R18.** Links to `CODE_OF_CONDUCT.md`.
- 🟡 **R19.** Describes the release process at a high level.

### Template

````markdown
# Contributing to <repository-name>

Please read our [Code of Conduct](./CODE_OF_CONDUCT.md) first.

## Branching

<Strategy, base branch, branch naming, maximum branch lifetime, merge method.>

## Commit messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

    feat(imports): support CSV files larger than 4 GB
    fix(mapping): keep shared references in template responses
    docs(adr): record decision to use Azure Service Bus

## Pull requests

Every PR requires:

1. A green pipeline (build, tests, docs gates).
2. <N> approval(s) from <team or group>.
3. For public API changes: approval from <leads group>.
4. A CHANGELOG entry under `[Unreleased]`.
5. Documentation updates for any behavior change.

PRs are merged with <squash | merge commit | rebase>. <If squash: the PR title becomes the commit message, so it follows Conventional Commits.>

## Local setup

See [README.md](./README.md#run-locally). To run the tests:

```bash
dotnet test
```

## Releases

<How versions are cut and published.>

## Reporting security issues

Do **not** open a public issue. <Contact, or see [SECURITY.md](./SECURITY.md).>
````

## 4. CODE_OF_CONDUCT.md

- 🟡 **R20.** Present in every repository open to contribution. Default text: [Contributor Covenant](https://www.contributor-covenant.org/). Insert the canonical text; do not paraphrase it.
- 🟡 **R21.** Names a real, monitored contact channel for violations. Ask the user for it; never invent one.

## 5. LICENSE

- 🔴 **R22.** Present in every repository, including internal ones. For internal-only code, state `Proprietary - Internal use only` or reference the organizational license statement.
- 🔴 **R23.** Contains the canonical license text itself, never only a link or a paraphrase.

Internal default:

```text
Copyright (c) <YYYY> FAVV-AFSCA. All rights reserved.

Proprietary - Internal use only.
```

## 6. Optional companion files

- 🟢 **R24.** `SECURITY.md`: vulnerability disclosure policy.
- 🟢 **R25.** `SUPPORT.md`: where to get help (not the issue tracker).
- 🟢 **R26.** `AUTHORS.md` or `MAINTAINERS.md`: finer-grained ownership.

## 7. Review checklist

- [ ] README answers what, status, owner, run locally and docs link on the first screen, and is under ~150 lines.
- [ ] No "see the wiki" as the only documentation pointer.
- [ ] CHANGELOG follows Keep a Changelog, semver, ISO dates, human-written entries with PR numbers, `[Unreleased]` on top.
- [ ] Breaking changes are listed and the version is a MAJOR bump.
- [ ] CONTRIBUTING covers branching, commits, PR process, local setup and security reporting.
- [ ] LICENSE contains actual text.

## 8. Pivot.Framework repository specifics

- **LICENSE:** the framework is licensed **AGPL-3.0-only** (`PackageLicenseExpression` in `Directory.Build.props`, full text in `LICENSE`). Services consuming it must check the AGPL obligations with their legal owner before shipping; record the outcome in an ADR. Never replace the framework's license text with the internal proprietary default.
- **README:** must state the package list, the GitHub Packages feed (`https://nuget.pkg.github.com/AnnabiGihed/index.json`) and the publishing flow (tag `vX.Y.Z` → `publish.yml`). Code samples must compile against the current source — the known drift is listed in the `pivot-framework` skill.
- **CHANGELOG:** one changelog for all packages (they share one version); entries name the package in backticks (`Pivot.Framework.Containers.API`: …). Anything that changes persisted tables, RabbitMQ wire format, DI registrations or `Result` semantics is a `### Breaking changes` entry.
- The repository currently has no `CHANGELOG.md` or `CONTRIBUTING.md` — create them before the next tagged release (R8, R16).
