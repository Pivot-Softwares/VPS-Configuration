---
name: credentials-policy
description: >-
  Mandatory whenever a token, key, password, certificate or any other credential is created, used, stored, rotated or
  removed, on GitHub, the VPS, OVH, name.com, Zoho, Docker registries, package feeds or the owner's PC. Personal
  access tokens and tokens that need manual renewal are forbidden; every other credential is flagged ⚠️, justified,
  registered and stored in the narrowest place.
---

# Credentials policy

The old setup failed on credentials: personal access tokens everywhere, configured by hand, on the server and the
owner's PC. This repository's rule, set by the owner on 2026-10-06 (ADR-0001):

- **Forbidden:** personal access tokens (classic or fine-grained) and any token that must be renewed or maintained by
  hand.
- **Allowed, always flagged:** credentials that are secure and need no manual maintenance, for example an SSH key, a
  deploy key, a GitHub App private key that only mints short-lived tokens, or short-lived tokens issued per run (OIDC).
- **Every** credential the plan needs is flagged ⚠️ at the moment it is proposed, and reviewed in detail with the owner
  when it is configured.

## Triggers

- A design, workflow, script, runbook or application change that needs to authenticate to anything.
- A credential found in a file, a log, an issue, a pull request or a command output.
- Removing the old setup's tokens (from the server, GitHub, Azure DevOps or the owner's PC).

## Required inputs

- What must authenticate to what, and with which permissions.
- The credential register, `docs/reference/credentials.md`, once it exists.

## Preflight checks

1. Prefer no credential at all: a public resource, the built-in `GITHUB_TOKEN`, or a platform identity (OIDC trusted
   publishing) beats a stored secret.
2. Then prefer a credential that can't expire silently and can't be used outside its scope: a key bound to one
   repository, one environment, one account, one host.

## Actions

1. **Flag it** in the proposal, the issue, the pull request's Credentials line and the ADR, with this block:

   ```markdown
   > ⚠️ **Credential:** <name>. Grants <what> to <whom>. Stored in <where>. Expires: <never / after N>.
   > Rotation: <none needed / how>. Revocation: <where to revoke it>. Why it is needed: <reason>.
   ```

2. **Choose where it lives**, narrowest first:
   - a GitHub **environment** secret, with deployment branches limited to `main` and, for production, a required
     reviewer; never a repository or organization secret when an environment works;
   - on the VPS, only what a running application needs at run time, readable only by that application's account,
     never in a Git checkout, an image or a log, and never a credential that reaches another system (GitHub, OVH, DNS,
     mail or a registry). **One owner exception (2026-10-07, #37):** the delivery template App's private key and
     webhook secret live on the VPS, because the owner chose to host the App there; ADR-0002 (#40) defines how they
     are protected;
   - on the owner's PC, only through a tool's own sign-in store (for example the Windows credential store), never as
     plain environment variables.
3. **Register it** in `docs/reference/credentials.md`: name, purpose, scope, location, owner, expiry, rotation and
   revocation steps, and the ADR that justified it. The register holds no secret values.
4. **Pass it safely:** through the step's environment or standard input, never on a command line, in a URL, in an
   issue or in a workflow log; GitHub masks secrets in logs only when they are passed as secrets.
5. **Removing a credential:** revoke it at its issuer first (the issuer is where it dies everywhere at once), then
   delete the stored copies, then update the register.

## Prohibited actions

- Creating, requesting or using a personal access token, even "temporarily".
- Asking the owner for a secret value, printing one, or handling one in the session.
- Committing a secret, even to a draft branch; a committed secret is revoked, never just deleted.
- Storing a credential on the VPS that grants access to another system.
- Long-lived cloud keys where the provider offers OIDC or a scoped, expiring alternative.

## Outputs and evidence

- The ⚠️ block on every proposal that needs a credential, and the register entry.
- For a removal, the revocation evidence (the issuer's page shows it gone), without the value.

## Failure behavior

- If no allowed credential type can do the job, stop and present the options with `decision-options`, including the
  forbidden one only to show why it is excluded.
- If a secret leaks, tell the owner at once with the revocation step; revoke first, investigate after.

## Sources

- Owner instructions (2026-10-06), recorded in ADR-0001.
- [GitHub environments](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment),
  [GitHub Apps installation tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app).
