---
name: docs-quality-gates
description: FAVV-AFSCA documentation review, linting and publishing rules. Use when reviewing a pull request that touches documentation, when creating or editing a documentation CI/CD pipeline (Azure Pipelines or GitHub Actions), markdownlint, Vale, lychee or Spectral configuration, when setting up preview deployments, or when publishing a documentation site with MkDocs Material and mike.
---

# Documentation Review, Linting and Publishing

Source: Development Standards Wiki → *Documentation Review, Linting, and Publishing*. Cite rules as `Documentation Review, Linting, and Publishing / R<n>`. Severity handling follows `docs-standards-governance`.

## 1. Review

- 🔴 **R1.** Documentation changes get PR review like code, with at least one approval.
- 🟡 **R2.** PRs introducing a new public feature also need a documentation reviewer (technical writer, team lead or designated doc owner).
- 🟡 **R3.** When reviewing documentation, check each item and report failures with a rule citation:
  - [ ] Technically accurate against the code in the same PR.
  - [ ] No "TODO" or "TBD".
  - [ ] No jargon that is not defined in the glossary or at first use.
  - [ ] Terminology consistent with the rest of the repository.
  - [ ] At least one example for every non-trivial concept.
  - [ ] No broken links.
- 🟡 **R4.** A separate, faster `docs-only` pipeline may run when only `*.md` or `docs/**` change.

## 2. Markdown linting

- 🔴 **R5.** Every Markdown file passes `markdownlint-cli2` with the shared organizational configuration.
- 🔴 **R6.** It runs in CI and fails the build.
- 🟡 **R7.** The configuration enforces ATX headings, a single top-level heading, fenced code blocks with language, `-` and `1.` list markers, headings no deeper than `####`, and 120-character lines (or semantic line breaks).
- 🟢 **R8.** A rule may be disabled for one file with an inline directive, always preceded by a comment explaining why:

  ```markdown
  <!-- Azure DevOps wiki page: the title comes from the file name, so there is no H1. -->
  <!-- markdownlint-disable MD041 -->
  ```

Reference configuration (extend the shared one from `favv-afsca/engineering-configs` rather than copying):

```yaml
# .markdownlint-cli2.yaml
config:
  default: true
  MD013: { line_length: 120, code_blocks: false, tables: false }
  MD024: { siblings_only: true }
  MD033: { allowed_elements: [br, details, summary, sub, sup] }
  MD041: true
  MD046: { style: fenced }
globs:
  - "**/*.md"
ignores:
  - "node_modules"
  - "CHANGELOG.md"
```

## 3. Prose linting

- 🟡 **R9.** Prose is linted with Vale using the organizational styles.
- 🟡 **R10.** The styles enforce organizational terminology ("API key", "GitHub", "OpenAPI", "REST API"), discourage "simply", "just", "obviously", require inclusive language, and warn on passive voice in guides and tutorials.
- 🟢 **R11.** The configuration may extend the Microsoft or Google Vale styles.
- 🔴 **R11a.** Vale errors fail the pull request; annotations alone are not a gate. `vale-action` reports through
  reviewdog, which only annotates the diff and still passes unless `fail_on_error: true` is set. Always set
  `fail_on_error: true` with `fail_level: error` and `filter_mode: nofilter`, so errors anywhere in the checked files
  fail the job. The CLI (`vale docs/`) fails on errors by itself. After adding or changing the step, prove it can
  fail: the run log shows `fail_on_error: true`, or a deliberate misspelling on a branch fails the check.
- 🔴 **R11b.** Vocabulary entries (`.vale/styles/config/vocabularies/<Name>/accept.txt`) are case-sensitive regular
  expressions. Add the capitalized form of a term that starts sentences (`mockup` and `Mockup`), and plurals Vale
  doesn't infer (`SVGs`). Add only genuine terms; never add a word to hide a misspelling.

```ini
# .vale.ini
StylesPath = .vale/styles
MinAlertLevel = suggestion
Packages = Microsoft, write-good

[*.md]
BasedOnStyles = Vale, Microsoft, write-good
Microsoft.We = warning
Microsoft.Passive = suggestion
```

## 4. Link checking

- 🔴 **R12.** Internal links are checked on every PR with `lychee` (or `markdown-link-check`); a broken internal link fails the build.
- 🟢 **R13.** External links are checked on a schedule (daily or weekly), never per PR.
- 🟡 **R14.** The scheduled check opens an issue listing broken links.

## 5. Required files and contracts

- 🔴 **R15.** CI fails if `README.md`, `CHANGELOG.md` or `LICENSE` is missing from the root.
- 🔴 **R16.** CI validates `openapi.yaml` / `openapi.json` when present (`redocly lint` or `swagger-cli validate`).
- 🟡 **R17.** CI checks `CONTRIBUTING.md` exists when the repository accepts outside contributions.

```bash
for f in README.md CHANGELOG.md LICENSE; do
  [ -f "$f" ] || { echo "##vso[task.logissue type=error]Missing required root file: $f"; exit 1; }
done
```

## 6. Snippet validation

- 🟡 **R18.** Snippets are validated in CI by compile-checking extracted snippets, by doctests, or by extracting them from tested files at build time.
- 🔴 **R19.** A snippet copied by hand into documentation consumed by external users and left to drift is FORBIDDEN. For such docs, use extraction (MkDocs `pymdownx.snippets`, DocFX code references) from files that the test suite compiles.

## 7. Preview deployments

- 🟡 **R20.** Every PR publishes a rendered preview.
- 🟡 **R21.** The preview URL is posted as a PR comment automatically.
- 🟢 **R22.** Previews may be torn down 24 hours after the PR closes.

## 8. Publication

- 🔴 **R23.** Docs are published automatically on every merge to the default branch. Never propose a manual or laptop-run deploy step.
- 🔴 **R23a.** When the repository host has a wiki (GitHub Wiki, Azure DevOps project wiki), it is a **generated mirror of `/docs`**, published by the same pipeline on every merge. This is mandatory, not optional:
  - `/docs` stays the only source. Nobody writes or edits wiki pages by hand; each publication replaces them.
  - Every generated page states that it is generated and links to the source file to edit.
  - Links between documents are rewritten to wiki pages, links outside `/docs` to the repository, and referenced images are copied.
  - The wiki's navigation (GitHub `_Sidebar.md`, Azure DevOps `.order`) is generated from the site navigation, which lists every document.
  - Every PR builds the wiki in the docs check and fails on a broken link, two documents with the same page name, or a document missing from the navigation.
  - Publication uses the pipeline's built-in credential (`GITHUB_TOKEN` with `contents: write`, or the Azure DevOps build service), never a personal token, and skips the push when nothing changed.
  - An enabled wiki that stays empty is a defect: publish into it, or disable it.
- 🔴 **R24.** The pipeline is defined in the repository: `.azuredevops/pipelines/docs.yml` for Azure DevOps, `.github/workflows/docs.yml` for GitHub.
- 🟡 **R25.** Preview, staging and production use the same pipeline definition.
- 🟡 **R26.** Published docs are versioned with a version switcher; with MkDocs use `mike`.
- 🟡 **R27.** Docs are served from a stable organizational URL (`https://docs.<org domain>/<project>/`), never a personal or temporary domain.
- 🟡 **R28.** Non-trivial docs use a static site generator. Default **MkDocs Material**; alternatives Docusaurus, Hugo, Sphinx, Antora.
- 🟡 **R29.** The site has search.
- 🟢 **R30.** Basic traffic analytics (Application Insights, Plausible, GoatCounter).
- 🟢 **R31.** A "Was this page helpful?" widget whose negative votes feed an issue queue.

## 9. Pipeline templates

### Azure Pipelines

```yaml
# .azuredevops/pipelines/docs.yml
trigger:
  branches:
    include: [main]
  paths:
    include: [docs/**, mkdocs.yml, README.md, CHANGELOG.md, openapi.yaml]

pr:
  branches:
    include: [main]

pool:
  vmImage: ubuntu-latest

stages:
  - stage: Validate
    jobs:
      - job: Lint
        steps:
          - task: NodeTool@0
            inputs: { versionSpec: '20.x' }
          - script: |
              for f in README.md CHANGELOG.md LICENSE; do
                [ -f "$f" ] || { echo "##vso[task.logissue type=error]Missing $f"; exit 1; }
              done
            displayName: Required root files
          - script: npx markdownlint-cli2 "**/*.md" "#node_modules"
            displayName: Markdown lint
          - script: docker run --rm -v $(pwd):/docs -w /docs jdkato/vale:latest --glob='*.md' docs/
            displayName: Prose lint (Vale)
          - script: |
              docker run --rm -v $(pwd):/input -w /input lycheeverse/lychee:latest \
                --no-progress --offline --include-verbatim docs README.md
            displayName: Internal link check
          - script: npx @redocly/cli@latest lint openapi.yaml
            displayName: OpenAPI lint
            condition: and(succeeded(), eq(variables['hasOpenApi'], 'true'))

  - stage: PublishPreview
    condition: and(succeeded(), eq(variables['Build.Reason'], 'PullRequest'))
    jobs:
      - deployment: Preview
        environment: docs-preview
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                - script: pip install mkdocs-material && mkdocs build --strict
                - task: AzureStaticWebApp@0
                  inputs:
                    app_location: site
                    skip_app_build: true

  - stage: PublishProduction
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: Production
        environment: docs-production
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                - script: |
                    pip install mkdocs-material mike
                    mike deploy --push --update-aliases $(projectVersion) latest
```

Set `hasOpenApi` from a previous step (`test -f openapi.yaml`) or remove the step in repositories without an API.

### GitHub Actions (validation stage)

```yaml
# .github/workflows/docs.yml
name: docs
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
    paths: ['docs/**', 'mkdocs.yml', 'README.md', 'CHANGELOG.md', 'openapi.yaml']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - name: Required root files
        run: for f in README.md CHANGELOG.md LICENSE; do test -f "$f" || { echo "::error::Missing $f"; exit 1; }; done
      - name: Markdown lint
        run: npx markdownlint-cli2 "**/*.md" "#node_modules"
      - name: Prose lint (Vale)
        uses: vale-cli/vale-action@v3
        with:
          files: docs
          filter_mode: nofilter
          fail_level: error
          # Without this, reviewdog only annotates Vale's errors and the job passes (R11a).
          fail_on_error: true
      - name: Internal link check
        uses: lycheeverse/lychee-action@v2
        with: { args: --offline --include-verbatim docs README.md }
      - name: OpenAPI lint
        if: hashFiles('openapi.yaml') != ''
        run: npx @redocly/cli@latest lint openapi.yaml
```

Pin action and tool versions according to the organization's supply-chain policy before merging.

## 10. Anti-patterns to reject

- "Ask Alice to run `./deploy-docs.sh`" or any manual publication step.
- A PR changing `docs/**` where CI runs only code tests.
- Documentation hosted on a personal subdomain.
- A lint or check step that reports problems without failing: reviewdog or SARIF annotations with
  `fail_on_error: false`, `continue-on-error: true`, `|| true`, a tool run with its exit code ignored (R11a), or a
  static-analysis status such as SonarCloud's whose quality gate passes while it lists findings. A green
  check with red annotations is a broken gate.
- A hand-written or hand-edited wiki page, a wiki that differs from `/docs`, or an enabled wiki left empty (R23a).
