---
name: owner-runbook
description: >-
  Mandatory whenever the owner must do something the agent can't: a command on the VPS, a setting in the OVH Control
  Panel, name.com, Zoho, GitHub or the Pivot-Softwares organization, or a step on the owner's Windows PC. Covers the
  runbook files in docs/how-to/, giving steps one at a time in the chat, read-only state checks, never locking the
  owner out, rollback for each step, and recording the evidence.
---

# Owner runbook

The agent has no access to the VPS or to any provider console (`vps-conventions` §8). Automation is the priority: a
step the owner runs by hand needs a reason, and the runbook is written so the step can later be automated or run
again without thinking.

## Triggers

- A change needs a command on the VPS, a provider console setting, a GitHub setting the API can't change, or a step
  on the owner's PC.
- The agent needs to know the server's current state.

## Required inputs

- The work item and the decision records the step applies.
- What the owner uses to reach the system: ask before the first step that depends on it (for example how they open
  an SSH session from Windows, or whether they use the OVH KVM console).

## Preflight checks

1. Is there a way to do it without the owner (a workflow, an API the session may call)? If so, use it.
2. Can the step lock the owner out (SSH, firewall, users, sudo, network)? Then plan the safety net first: keep an
   existing session open while testing a new one, and know the OVH KVM console or rescue mode route back in.
3. Does the step need a credential? Flag it (`credentials-policy`); the owner types secrets, never the agent.

## Actions

1. **Write the runbook** as `docs/how-to/<task>.md` in the task's pull request, with these sections:
   - **Purpose** and the decision records it applies;
   - **Before you start:** what must already be true, and the safety net;
   - **Steps**, numbered, each with: what to do, **where** (which program, which console page, PowerShell or the
     server, as which user), **why** in one sentence, the exact command or click path, and **what you should see**;
   - **Check:** read-only commands that prove the result;
   - **Undo:** how to put each step back;
   - **Automation:** what would replace the manual step, or why it stays manual.
2. **Give the steps in the chat one at a time.** Wait for the owner's report and read it before the next step. Never
   paste the whole runbook as one message to execute.
3. **Learn the state with read-only commands** that print no secret, and ask the owner to paste the output. Check from
   outside what can be checked from outside: DNS, HTTPS and certificates, SSH authentication methods, open ports.
4. **Make every step safe to rerun:** check before changing, only add what is missing, and say what to do if the output
   differs from the expected one.
5. **Record the evidence** on the work item: the commands run (without secrets) and the outputs that prove the result.

## Prohibited actions

- Signing in to the VPS or any console, or asking for credentials, one-time codes or recovery keys.
- Steps that disable the firewall, enable password sign-in, or remove the last working way in, even briefly.
- Commands piped from the internet into a shell (`curl ... | sh`) without the owner seeing the script and its source.
- Steps that assume a fresh machine without checking.

## Outputs and evidence

- The runbook in `docs/how-to/`, linked from the ADR it applies.
- The owner's pasted outputs, recorded on the work item.

## Failure behavior

- If an output differs from the expected one, stop, explain what it means, and give the read-only command that
  narrows it down. Never guess the next step.
- If the owner is locked out, the first step is the recovery route (OVH KVM console or rescue mode), not a fix.

## Sources

- `AnnabiGihed/RaidManager` `raidmanager-conventions` §13 (owner steps one at a time, read-only state, no sign-in).
- [OVHcloud VPS documentation](https://help.ovhcloud.com/csm/en-vps-getting-started).
