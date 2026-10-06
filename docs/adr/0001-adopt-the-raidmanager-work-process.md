# ADR-0001: Adopt the RaidManager work process for the VPS configuration

- Status: Proposed
- Date: 2026-10-06
- Deciders: Gihed Annabi

## Context

The OVH VPS (2 vCores, 4 GB memory, 40 GB storage) hosts three applications under `pivotsoftwares.com`, from
`AnnabiGihed/RaidManager`, `AnnabiGihed/Delivery-Atlas` and `AnnabiGihed/PivotSoftwarsWebsite`. Its configuration for
Azure DevOps (agent pools, hooks, pipelines) became messy, relied on personal access tokens, and left its security in
doubt. The owner decided to reset the VPS and rebuild its security and the three deployments from scratch, documented
and automated from this repository.

RaidManager already runs a complete work process: the
[Work Management and Delivery Specification](../reference/work-management-specification.md), its skills, issue forms,
Project fields and views, guard workflows and review gates. The owner asked for the same process here, and set the
rules below in the planning session of 2026-10-06. The options considered for each open point were:

1. **Who operates the Project's fields:** the owner's local `gh` login as in RaidManager; the agent creates issues and
   the owner sets fields by hand; or an organization Project operated by a GitHub App.
2. **Who owns what on the server:** this repository owns the shared platform and each application owns its
   deployment; or each repository provisions its own part of the server.
3. **How much of RaidManager's process to copy:** the whole process with code-only gates (coverage, SonarCloud,
   Penpot) replaced by infrastructure checks; or everything unchanged.
4. **How to start under the rules:** a bootstrap work-item chain first; or an owner exception for the first skills.

## Decision

We adopt RaidManager's work process for `Pivot-Softwares/VPS-Configuration`, with these owner decisions of
2026-10-06:

- **Scope:** the VPS is reset; nothing is backed up from the old installation; every configuration is redone from
  scratch, including in the deployed repositories. Downtime is accepted. Azure DevOps is not used at all; everything is
  on GitHub.
- **Process (decision C):** the specification, the eight `work-*` skills, the hierarchy, the issue forms, the Project
  fields and views, the guard, the review and merge gates, the documentation checks and publishing, Dependabot tasks,
  deployment labels, identical skill trees and Conventional Commits are copied. Coverage, SonarCloud and Penpot gates
  are replaced by infrastructure checks: shellcheck, actionlint, YAML lint and secret scanning.
- **Project (decision A, with F):** the repository and its Project belong to the `Pivot-Softwares` organization. The
  owner copied the Raid Manager Project into the organization. The agent operates the Project's fields through a board
  bridge workflow and the `pivot-board-bridge` GitHub App (specification amendment A11).
- **Ownership (decision B):** this repository owns everything shared on the server; each application repository owns
  its own deployment. Pull requests, never direct pushes, are allowed in the application repositories.
- **Credentials:** personal access tokens, and any token that needs manual renewal, are forbidden. A credential that
  is secure and needs no maintenance (SSH keys, deploy keys, a GitHub App key) is allowed, and every credential is
  flagged and reviewed in detail when it is configured. Application secrets live in GitHub environments, decided one
  by one; the VPS holds only what a running application needs.
- **DNS (decision H):** DNS stays at name.com, managed by hand by the owner from the agent's exact instructions. Mail is
  Zoho's and must keep working.
- **Monitoring, alerts and backups:** in scope when free and light on the server. Automatic operating-system updates
  are in scope. Security of the VPS has the highest priority.
- **Environments:** staging is used only for RaidManager, with dev, test and production; the other applications run
  production only.
- **Pivot.Framework (decision G):** its packages move to a free, public feed that needs no credential to read, if they
  can be public, so RaidManager stops needing a personal token.
- **People:** the owner `@AnnabiGihed` is the operator; `@anthermook` is the peer reviewer.
- **Bootstrap (decision E, extended the same day):** the first version of the skills, then the board foundation (the
  board bridge, the issue forms, the type and rule labels and the hierarchy guard), are delivered without work items;
  the first epic, feature and story are created right after and link these pull requests as history. Later changes
  need their work items.
- **Sprint 1** runs from 2026-10-06 00:00 to 2026-10-20 00:00 Europe/Brussels.
- **Decisions and documentation:** the agent never decides; it gives options with a recommendation. Every
  configuration is documented in `docs/` with why it was chosen, its pros and cons, and how it was done. The agent has
  no access to the VPS; the owner runs every step on it, one at a time. Automation is preferred to manual steps.

## Consequences

**Positive**

- One process across RaidManager and the platform; the owner reads the same board, records and reviews everywhere.
- No personal token anywhere in the new setup; each remaining credential is visible, justified and registered.
- Every platform choice is recorded with its reasons and trade-offs, so a later reset can be replayed.

**Negative**

- The process is heavy for a one-server platform: every change needs a task, a sprint and two reviews.
- The board bridge adds a workflow and a GitHub App key to secure, and a run's delay to every field change.
- The RaidManager server files and items must be moved here through coordinated pull requests in both repositories.
- Until the repository visibility is settled, branch protection and documentation publishing may be unavailable on
  the Free organization plan.

## Alternatives considered

- **The owner's local `gh` login, as in RaidManager** — rejected: the agent works from cloud sessions, which can't use
  it, and the owner wants the agent to operate the fields.
- **The owner sets every field by hand** — rejected: it moves routine board work onto the owner.
- **Each repository provisions its own part of the server** — rejected: shared settings would drift between
  repositories.
- **Copy RaidManager's process unchanged** — rejected: its coverage, SonarCloud and mockup gates don't fit a repository
  with no application code.
