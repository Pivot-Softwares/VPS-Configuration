---
name: docs-as-code
description: FAVV-AFSCA Documentation as Code rules. Use whenever you write or edit any Markdown documentation, decide where documentation belongs in a repository, or make a code change that alters observable behavior (public API, CLI, configuration, build output) and therefore needs a documentation update in the same pull request. Covers the /docs folder and Diátaxis layout, writing style, Markdown formatting that passes the linters, and code snippet rules.
---

# Documentation as Code

Source: Development Standards Wiki → *Documentation as Code*. Cite rules as `Documentation as Code / R<n>`. Severity handling follows the `docs-standards-governance` skill: always apply 🔴, apply 🟡 by default, apply 🟢 only when asked.

## 1. Core rules

- 🔴 **R1.** Documentation lives in the same repository as the code it describes. Only cross-cutting organizational docs (engineering handbook, onboarding) may live in a dedicated documentation repository.
- 🔴 **R2.** Write documentation in Markdown. AsciiDoc and reStructuredText are allowed only where a repository already uses them.
- 🔴 **R3.** `.docx`, `.pptx` and `.pdf` are FORBIDDEN as sources. They may only be produced as build outputs. If asked to document something in one of these formats, write Markdown in the repository and, if needed, add a pipeline step that exports it.
- 🔴 **R4.** A change to observable behavior MUST include its documentation update in the **same pull request**. See section 2.
- 🔴 **R5.** Documentation is versioned with the code; the docs published for `vX.Y.Z` reflect exactly that version.

## 2. Same-PR documentation matrix (R4)

Before finishing any code change, walk this table and include every matching update in the same change. Never leave it for a follow-up PR.

| The change... | Update in the same PR |
| --- | --- |
| Adds, removes or changes a public or internal API operation, request, response or status code | `openapi.yaml` / `asyncapi.yaml` / `.proto` / SDL (`docs-api-contracts`), `CHANGELOG.md` |
| Changes a public type or member of a library | XML doc comments on the member, `CHANGELOG.md` |
| Adds, removes or changes a configuration key, default value or environment variable | `docs/reference/configuration.md` (or its generating schema), `CHANGELOG.md` |
| Changes a CLI command, flag or output | `docs/reference/` page for the CLI, `CHANGELOG.md` |
| Changes the build output, package name or deployment artifact | `README.md` run instructions, `CHANGELOG.md` |
| Adds, removes or rewires a service, database, queue or external dependency | Diagrams in `docs/diagrams/` (`docs-diagrams-as-code`) |
| Makes a decision listed in `Architecture Decision Records / R1` | A new ADR (`docs-adr`) |
| Breaks backward compatibility | `### Breaking changes` entry in `CHANGELOG.md`, MAJOR version bump, migration guide under `docs/how-to/` or `docs/migration/` |
| Changes local setup steps or prerequisites | `README.md` and `CONTRIBUTING.md` |

When reviewing a PR, a behavior change with none of its matching updates is a **Blocking** violation of `Documentation as Code / R4`.

## 3. Folder structure

- 🔴 **R6.** Extended documentation goes in a top-level `/docs` folder. Never create `/documentation`, `/doc` or `/wiki`.
- 🟡 **R7.** Inside `/docs`, separate content by Diátaxis type:

| Folder | Diátaxis type | Put a page here when it... |
| --- | --- | --- |
| `docs/tutorials/` | Learning-oriented | Walks a newcomer through a complete first experience, step by step |
| `docs/how-to/` | Task-oriented | Solves one concrete task for someone who already knows the system |
| `docs/reference/` | Information-oriented | Describes facts: endpoints, configuration keys, CLI flags, schemas (preferably generated) |
| `docs/explanation/` | Understanding-oriented | Discusses concepts, design and trade-offs |

  Also: `docs/adr/` for decision records, `docs/diagrams/` for standalone diagrams, `docs/index.md` as the landing page.
- 🟡 **R8.** A component or module with its own responsibility gets a `README.md` next to its code, in addition to anything in `/docs`.
- 🟢 **R9.** `docs/glossary.md` may hold domain terms.
- 🟡 **R14.** One page, one Diátaxis type. When a page mixes a tutorial, a reference table, a rationale and a runbook, split it into one page per folder.

### Canonical layout (.NET service)

```text
attribute-service/
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE
├── openapi.yaml
├── mkdocs.yml
├── docs/
│   ├── index.md
│   ├── tutorials/
│   ├── how-to/
│   ├── reference/
│   │   ├── api.md                 ← generated from openapi.yaml
│   │   └── configuration.md       ← generated from options classes / JSON Schema
│   ├── explanation/
│   ├── adr/
│   │   ├── README.md              ← ADR index
│   │   └── 0001-use-dotnet-and-azure-sql.md
│   ├── diagrams/
│   │   ├── context.mmd
│   │   └── container.mmd
│   └── glossary.md
├── src/
│   └── Attribute.Api/
│       └── README.md              ← component-level doc
├── tests/
└── .azuredevops/pipelines/docs.yml   (or .github/workflows/docs.yml on GitHub)
```

## 4. Writing style

- 🟡 **R10.** Active voice, second person singular: "Run the migration", "You configure the key in...". Not "The migration should be run" or "We run the migration".
- 🟡 **R11.** Short sentences, short paragraphs. Replace any enumeration of three or more items inside a sentence with a bulleted list.
- 🟡 **R12.** Define every acronym at first use on the page: "Architecture Decision Record (ADR)".
- 🟡 **R13.** Inclusive, translatable language. Do not use idioms, gendered terms ("guys"), or ableist metaphors ("sanity check" → "quick check", "dummy" → "placeholder"). Use "allowlist/denylist", "primary/replica".
- Do not use "simply", "just", "obviously", "easy" (`Documentation Review, Linting, and Publishing / R10`).
- Use organizational terminology: "API key", "GitHub", "OpenAPI", "REST API", "Azure DevOps".
- Never leave "TODO" or "TBD" in documentation you finish (`Documentation Review, Linting, and Publishing / R3`).

## 5. Markdown formatting (passes the organizational markdownlint config)

- Exactly one `#` heading per file, on the first line. Exception: Azure DevOps wiki pages, see `docs-standards-wiki-page`.
- ATX headings (`#`) only; do not go deeper than `####`.
- Unordered lists use `-`; ordered lists use `1.`.
- Every fenced code block declares a language (**R17**): `csharp`, `bash`, `powershell`, `yaml`, `json`, `xml`, `text`, `diff`, `mermaid`.
- Lines at most 120 characters, except inside code blocks and tables; or one sentence per line.
- Allowed inline HTML only: `<br>`, `<details>`, `<summary>`, `<sub>`, `<sup>`.
- Relative links for anything inside the repository (`./docs/how-to/rotate-keys.md`), never absolute links to the repository host.

## 6. Code examples

- 🔴 **R15.** Every snippet must run as-is once the prerequisites listed on the page are met. Write the prerequisites on the page. Anything that is not runnable must be introduced with the sentence "The following is pseudo-code." and use the `text` language tag.
- 🟡 **R16.** Prefer pulling snippets from real, tested files (MkDocs snippet includes, Docusaurus imports, DocFX code references) over copying them by hand.
- 🟡 **R17.** Always declare the code block language.

## 7. Publication

- 🟡 **R18.** Projects with non-trivial documentation publish a static site. Default: **MkDocs Material**. Alternatives: Docusaurus, Hugo, Sphinx (Python-heavy), Antora (multi-repo).
- 🟡 **R19.** The site has search.
- 🔴 **R19a.** If the repository has a wiki, it is generated from `/docs` on every merge and never edited by hand (`docs-quality-gates` R23a). Every document therefore starts with its `#` title (the wiki page name) and appears in the site navigation (the wiki sidebar).

Pipeline and gate details: `docs-quality-gates`.

## 8. Anti-patterns to reject

- Documentation in Confluence, SharePoint or a `.docx` instead of the repository.
- A PR that changes behavior (for example a default timeout) with no changelog or reference update.
- A single page mixing tutorial, reference, rationale and runbook.
- "See the wiki" as the only pointer to documentation (`README, CHANGELOG, CONTRIBUTING / R5`).
- Content written directly in the wiki instead of `/docs` (R19a).

## 9. Merged from the former `docs-authoring` skill

The older house layout (`docs/Home.md`, `docs/Architecture/`, `docs/stories/`, `docs/howto/`, `docs/references/`) is
**superseded** by the Diátaxis layout above. When you meet it in an existing repository, don't create a parallel tree:
migrate incrementally (`Documentation Standards / R20`), one folder per PR, with this mapping:

| Old location | New location |
| --- | --- |
| `docs/Home.md` | `docs/index.md` (landing page: what it is, where to start, local build/run commands, links) |
| `docs/Architecture/Architecture-<Solution>.md` | `docs/explanation/architecture.md` (or the architecture proposal, see `architecture-proposal`) |
| `docs/Architecture/diagrams/*.mmd` | `docs/diagrams/*.mmd` |
| `docs/Architecture/assets/` | `docs/diagrams/` (rendered exports next to their sources) |
| `docs/architecture-decisions.md` | `docs/adr/README.md` (ADR index) |
| `docs/howto/` | `docs/how-to/` |
| `docs/references/` (OpenAPI, `.proto`, `api.md`) | `openapi.yaml` at the root or `docs/api/`, `Protos/` next to the code, generated `docs/reference/api.md` |
| `docs/stories/STORY-NN-*.md` | the work tracker (stories are the analyst's backlog, not documentation); keep only lasting design explanations in `docs/explanation/` |

Rules carried over: documentation language matches the repository's existing docs (never mix languages in one tree);
a README pointing only to "the wiki" is forbidden; snippets are runnable and language-tagged.

## 10. Documenting services built on Pivot.Framework

- Don't re-document the framework: link to the relevant `pivot-*` skill or the Pivot.Framework README section, and document only the service's choices (which drain mode, transport, read store, auth topology — each backed by an ADR).
- `docs/reference/configuration.md` lists every configuration section the service binds, including the framework ones: `ConnectionStrings:Default`/`Redis`/`HangfireConnection`, `Keycloak`, `RabbitMQ`, `TokenRevocation`, `MongoDB` — with defaults and which keys are secrets.
- `docs/explanation/` explains the messaging flow (outbox → transport → consumers) with the sequence diagram from `docs-diagrams-as-code` §12, adapted to the service.
- The Pivot.Framework repository itself documents its packages through `README.md` and the `.claude/skills/pivot-*` skills; any change to a package's public behaviour updates both in the same PR (R4). README content that disagrees with the source is a defect — fix it and update the drift table in `pivot-framework`.
