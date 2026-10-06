---
name: decision-options
description: >-
  Mandatory whenever a choice has a security, cost, architecture, tooling, process or operational consequence: never
  decide alone; present two to four options with the recommended one first, each with pros, cons and consequence;
  record the owner's choice on the issue and, for platform choices, as an ADR that says why it was chosen, its pros,
  its cons and how it was done.
---

# Decision options

The owner takes every decision in this repository ([ADR-0001](../../../docs/adr/0001-adopt-the-raidmanager-work-process.md),
`vps-conventions` §8). The agent's job is to make each decision easy and well informed, then record it so nobody has
to reconstruct it later.

## Triggers

- Any choice between tools, services, providers, operating systems, configurations, network layouts, deployment
  methods, credentials, schedules or costs.
- A request that conflicts with a rule, a record or an earlier decision.
- A missing fact that only the owner can supply (a preference, a budget, an account detail without its secret).
- Not a trigger: wording, file names and formatting inside an agreed structure; they stay visible in the pull request.

## Required inputs

- The question in one sentence, and the work item it belongs to.
- The constraints already decided: the ADRs in `docs/adr/`, the specification, `vps-conventions` §1 and §4, and the
  owner's standing rules (no personal tokens, every credential flagged, free and light on the 4 GB server where they
  said so, automation over manual steps, no agent access to the server).
- Current, sourced facts about each option: official documentation, prices and limits checked on the day.

## Preflight checks

1. Search the ADRs and the issue for an existing decision. Reuse it; don't ask twice.
2. Check that each option respects the standing rules. An option that breaks one is listed only if the comparison needs
   it, and is marked as breaking that rule.

## Actions

1. **Write the options**, two to four, the recommended one first and marked "(Recommended)". For each:
   - what it is, in one sentence;
   - **pros** and **cons**, concrete (cost, memory and CPU on the VPS, security, automation, maintenance);
   - the **consequence** of choosing it: what follows, what becomes impossible or harder;
   - every credential it needs, flagged ⚠️ (`credentials-policy`);
   - the sources checked, with the date.
2. **Give the recommendation and the reason** in one or two sentences tied to the owner's rules.
3. **Ask** with the question tool when the session has it (options as choices, the recommended one first), otherwise in
   the chat with numbered options. One decision per question; group at most four related questions.
4. **Record the answer before acting:** on the issue it settles, under
   `### Owner decisions (<date>, recorded here)`, quoting the choice.
5. **Platform decisions become ADRs** (`docs-adr`): `docs/adr/NNNN-<decision>.md`, status Proposed while the pull
   request is open and Accepted when it merges with the owner's review. The owner asked that every configuration be
   documented with:
   - **why it was chosen** (Context and Decision);
   - **its pros and cons** (Consequences, positive and negative);
   - **the alternatives** and why they lost (Alternatives considered, from the options of step 1);
   - **how it was done**: a link to the runbook or workflow that applies it, and to the evidence that it works.
6. Add the ADR to `docs/adr/README.md` and to `vps-conventions` §4 when it settles an open question.

## Prohibited actions

- Choosing, implementing or "temporarily" applying an option before the owner answers.
- Presenting a single option, or options that differ only in wording.
- Hiding a credential, a cost or a resource consumption in an option's description.
- Inventing a fact, a price or a limit; mark it `Unknown: to verify` and say how to verify it.
- Rewriting an Accepted ADR; supersede it with a new one.

## Outputs and evidence

- The question as asked, with its options, and the owner's answer recorded on the issue.
- The ADR, when the decision shapes the platform, linked from the issue and the pull request.

## Failure behavior

- If the owner doesn't answer, the item stays `Blocked` with the open question as its unblock condition; nothing that
  depends on it starts.
- If new facts invalidate a recorded decision, raise them with new options; never silently diverge.

## Sources

- Owner instructions for this repository (2026-10-06), recorded in ADR-0001.
- `AnnabiGihed/RaidManager` `raidmanager-conventions` §13; `docs-adr`.
