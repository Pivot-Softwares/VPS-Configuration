---
name: docs-standards-wiki-page
description: Exact page format for the FAVV-AFSCA Development Standards Wiki (Azure DevOps wiki). Use when writing, editing or reviewing any standards page, such as Documentation Standards or Clean Code pages; adding, changing or retiring a rule; adding Good/Bad examples; or maintaining the wiki's .order files. Covers file naming, the four fixed sections, rule numbering and severity markers, example format, links and Mermaid syntax.
---

# Development Standards Wiki Page Format

Every standards page follows the same structure so that rules can be cited as `<Page name> / R<n>` (`Documentation Standards / R8`). Changes go through a PR against the wiki repository with the reviews and CHANGELOG entry required by `docs-standards-governance` section 8.

## 1. Files

- The page title is the file name with spaces replaced by `-`, keeping commas and `&` spelled as in the title: `Diagrams as Code` → `Diagrams-as-Code.md`, `README, CHANGELOG, CONTRIBUTING` → `README,-CHANGELOG,-CONTRIBUTING.md`.
- Child pages live in a folder named like the parent page file without `.md`, next to it: `Documentation-Standards.md` + `Documentation-Standards/`.
- Each folder has a `.order` file listing its pages without extension, one per line, in reading order. Add every new page to it.
- There is no `#` heading: Azure DevOps uses the file name as the page title. The repository's markdownlint configuration disables MD041 for wiki pages.

## 2. Page skeleton

The page contains exactly these parts, in this order:

```markdown
**<Page title> - <Subtitle stating the scope in a few words>**

## 1. Short Description

<One paragraph, 3-6 sentences: what the standard covers, why it exists, what it requires in essence, and which sibling pages cover related topics.>

## 2. Keywords / Tags

`<tag-1>`, `<tag-2>`, `<tag-3>`

## 3. Rules & Recommendations

Legend: 🔴 Mandatory, 🟡 Recommended, 🟢 Optional.

### 3.1 <Topic>

- 🔴 **R1.** <Rule text>

### 3.2 <Topic>

- 🟡 **R2.** <Rule text>

## 4. Examples

### 4.1 ✅ Good - <What the example shows>

### 4.2 ❌ Bad - <What is wrong>
```

- The first line is the bold title line; nothing comes before it.
- Tags: lowercase kebab-case, each in backticks, comma-separated on one line.
- Subsections of section 3 are numbered `3.1`, `3.2`, ... and of section 4 `4.1`, `4.2`, ... consecutively. Never number a section 3 subsection as `4.x`.

## 3. Rules

- Format: `- 🔴 **R<n>.** <text>` with a blank line between rules. Sub-points are indented two spaces with `-`.
- The marker and the RFC 2119 keyword always agree:

| Marker | Keywords allowed in the rule text |
| --- | --- |
| 🔴 | MUST, MUST NOT, FORBIDDEN, NEVER |
| 🟡 | SHOULD, SHOULD NOT |
| 🟢 | MAY |

  A rule that needs MUST is 🔴. Never write MUST in a 🟡 or 🟢 rule, or SHOULD in a 🔴 rule.
- One requirement per rule. Split rules that combine two obligations.
- Numbering runs `R1`, `R2`, ... across the whole page, in order of appearance, on a new page.
- **On an existing page, never renumber.** Rule IDs are cited in PRs and ADRs. A new rule takes the next number after the highest number ever used on the page, even when placed in an earlier subsection. A removed rule stays in place as `- ~~**R<n>.**~~ Retired on <YYYY-MM-DD> (<PR link>). <One-line reason.>`.
- Cross-references use the citation form: "Per **R10**" within the page, `Diagrams as Code / R8` across pages.
- Every rule is testable: a reviewer can say whether a given change complies. Replace vague words ("appropriate", "good", "clean") with the concrete criterion.
- Principles that explain rules but are not enforceable are labeled `P1`, `P2`, ... and stated as such in their subsection.

## 4. Examples

- Every 🔴 rule is illustrated by at least one example, Good or Bad.
- Good example heading: `### 4.<n> ✅ Good - <title>`, followed by the example and one sentence stating why it is good.
- Bad example heading: `### 4.<n> ❌ Bad - <title>`, followed by the example, then:

  ```markdown
  Why this is bad:

  - <Consequence, citing the rule: "Violates **R8**.">

  Correct approach: <what to do instead, or a reference to a Good example>.
  ```

- Good examples come before Bad examples.
- Use FAVV-AFSCA domain examples (attribute templates, inspections, authentic sources, import jobs) and the organization's stack (.NET, Azure, Azure DevOps, GitHub Enterprise) rather than generic ones.
- Code blocks always declare a language. To show Markdown that itself contains a code fence, open the outer block with four backticks.

## 5. Links and diagrams

- Links to other wiki pages are relative wiki paths: `[Diagrams as Code](./Documentation-Standards/Diagrams-as-Code)`. Check that the target path exists in the repository before adding it.
- Mermaid blocks use the Azure DevOps syntax `::: mermaid` … `:::` and only the diagram types allowed by `Diagrams as Code / R7` (see `docs-diagrams-as-code`).

## 6. Checklist

- [ ] File name matches the title; the page is listed in `.order`.
- [ ] Bold title line first, then sections 1-4 with the exact headings above.
- [ ] Every rule has a marker, a bold `R<n>.`, and a keyword matching its marker.
- [ ] No existing rule was renumbered; retired rules are marked, not deleted.
- [ ] Subsection numbers match their section.
- [ ] Every 🔴 rule has an example; every Bad example has "Why this is bad" and "Correct approach".
- [ ] A CHANGELOG entry and the required reviewers are listed in the PR (`docs-standards-governance`).
