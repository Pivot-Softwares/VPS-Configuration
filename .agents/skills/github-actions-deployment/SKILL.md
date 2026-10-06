---
name: github-actions-deployment
description: >-
  Use for every GitHub Actions workflow that builds, configures or deploys anything to the VPS, in this repository or
  an application repository: environments and their protection, how the runner reaches the server, secrets delivery,
  serialized deployments, health checks and rollback, deployment labels on work items, and workflow security
  (permissions, pinned actions, untrusted input).
---

# GitHub Actions deployment

Everything is on GitHub; Azure DevOps isn't used (owner decision, ADR-0001). Automation is the priority: a merge or an
approved run should change the server, not a person typing on it. How the runner reaches the server is a
**decision** (`decision-options`): the usual options are SSH from a GitHub-hosted runner with a pinned host key, the
server pulling released images itself, or a self-hosted runner. Each needs a different credential (`credentials-policy`).

## Triggers

- Writing or changing a workflow that touches the server, a GitHub environment, or deployment secrets.
- A failed deployment, or a change to the deployment labels.

## Required inputs

- The accepted deployment ADR, the environment names (RaidManager: dev, test and production; Delivery Atlas and the
  website: production), and each application's health check.
- RaidManager's `deploy-dev.yml` and Delivery Atlas's `deploy.yml`, which already implement most rules below.

## Preflight checks

1. The workflow's `permissions:` grant only what each job needs, starting from `contents: read`.
2. Every third-party action is pinned to a full commit id, with its version in a comment; Dependabot proposes updates.

## Actions

1. **One GitHub environment per target**, with deployment branches or tags restricted (`main` for dev, release tags
   for test and production) and a required reviewer for production. Secrets live in the environment.
2. **Reach the server with the least power:** one deploy account and one key per application environment; the host
   key pinned in a variable (`StrictHostKeyChecking=yes`), never accepted on first use. Prefer a key restricted to a
   forced command on the server (**decision**). A self-hosted runner on this server is not used for public
   repositories: anyone who can open a pull request could run code on it.
3. **Deliver secrets through standard input or the job environment**, never on a command line or in the log; write
   them on the server with `umask 077`, readable by the application account only.
4. **Serialize deployments** with `concurrency` per environment, and skip a run superseded by a newer commit.
5. **Build and test before touching the server**; a failed build leaves the running version in place.
6. **Health check from outside after each deployment**, through the proxy, and put the previous version back
   automatically on failure.
7. **Record what was delivered** on the work items: the `deployed:<environment>` and `deploy-failed:<environment>`
   labels and the release milestone line (spec §22, A9, A10), set by the workflow only.
8. **Treat event data as untrusted:** pass `${{ }}` values through `env:` instead of inlining them in `run:`, and never
   use `pull_request_target` with a checkout of the pull request's code.

## Prohibited actions

- Personal access tokens anywhere in a workflow; repository-wide secrets where an environment works.
- `StrictHostKeyChecking=no`, unpinned actions, `permissions: write-all`.
- Deploying from a branch other than the environment allows, or a manual `docker` command replacing a workflow run.

## Outputs and evidence

- The workflow, the environment settings as owner steps (`owner-runbook`), and a successful run with its health check.

## Failure behavior

- A failed deployment keeps or restores the previous version; the run's log and the item's `deploy-failed` label say
  what happened. Raise a bug with its task; never re-run until the cause is understood.

## Sources

- [Security hardening for GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions).
- `AnnabiGihed/RaidManager` `.github/workflows/deploy-dev.yml`, ADR-0027, ADR-0028;
  `AnnabiGihed/Delivery-Atlas` `.github/workflows/deploy.yml`.
