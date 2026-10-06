---
name: docs-adr
description: FAVV-AFSCA Architecture Decision Record rules. Use when a change involves a significant technical decision (database, broker, framework, protocol, architectural pattern, deployment target, auth scheme, API versioning, team-wide tooling), when asked to write, review, supersede or deprecate an ADR, when an exception or waiver to a Mandatory standard is needed, or when maintaining the ADR index. Covers when an ADR is required, numbering, the template, status lifecycle and immutability.
---

# Architecture Decision Records

Source: Development Standards Wiki → *Architecture Decision Records*. Cite rules as `Architecture Decision Records / R<n>`. Severity handling follows `docs-standards-governance`.

## 1. When an ADR is required

- 🔴 **R1.** Write an ADR for any of:
  - database, message broker, cache or other core infrastructure;
  - framework, language or major third-party library;
  - protocol (REST vs gRPC, sync vs async);
  - significant architectural pattern (event sourcing, CQRS, saga orchestration, hexagonal architecture);
  - deployment target (Kubernetes vs managed PaaS, single- vs multi-region);
  - authentication and authorization scheme;
  - API versioning strategy;
  - build, test and release tooling that affects the whole team;
  - an exception or waiver to a Mandatory documentation rule (`Documentation Standards / R4, R23`).
- 🟡 **R2.** Also write one whenever a future maintainer is likely to ask "why not X instead?".
- 🟢 **R3.** Not for version bumps, cosmetic refactors or local style preferences.

When a code change you are making falls under R1 and no ADR covers it, stop and tell the user an ADR is required; offer to draft it with status `Proposed`.

## 2. Location, numbering and names

- 🔴 **R4.** ADRs live in `docs/adr/`.
- 🔴 **R5.** File name: `NNNN-kebab-case-title.md`, four-digit sequential number: `0007-use-azure-service-bus-for-outbox.md`.
- 🔴 **R6.** Numbers are never reused. To pick the number, take the highest number that has ever existed in `docs/adr/` (check `git log --all --name-only -- docs/adr` for deleted files as well) and add one. Gaps are normal.
- 🟡 **R7.** Maintain `docs/adr/README.md` as an index and update it in the same PR as every new ADR or status change:

```markdown
# Architecture Decision Records

| #  | Title                                     | Status                  |
|----|-------------------------------------------|-------------------------|
| 1  | Use Azure SQL as the primary datastore    | Accepted                |
| 4  | Use RabbitMQ for the outbox               | Superseded by ADR-0014  |
| 14 | Use Azure Service Bus instead of RabbitMQ | Accepted                |
```

## 3. Template

- 🔴 **R8.** Mandatory header and sections. 🟡 **R9.** Recommended additional sections: *Alternatives considered* and, when replacing an ADR, the *Supersedes* line.

```markdown
# ADR-NNNN: <Decision title in present tense>

- Status: <Proposed | Accepted | Deprecated | Superseded by ADR-MMMM>
- Date: <YYYY-MM-DD>
- Deciders: <names or @handles>
- Supersedes: ADR-MMMM            ← only when replacing an ADR

## Context

<Forces at play: business requirements, technical constraints, existing systems, team skills.
List the options considered, numbered.>

## Decision

We <adopt | use | migrate to> <option>. <Precise scope and rules that follow from it.>

## Consequences

**Positive**

- <...>

**Negative**

- <...>

## Alternatives considered

- **<Option>** - rejected. <Reason.>
```

- Title: present tense, states the decision, not the question: "Use client-supplied idempotency keys for POST /payments", not "Idempotency strategy".
- 🟡 **R10.** *Context* describes the forces, not the solution.
- 🟡 **R11.** *Decision* uses active voice and imperative commitment: "We adopt X", "We use Y". Never "X might be a good fit".
- 🟡 **R12.** *Consequences* lists **both** positive and negative outcomes. An ADR with no negative consequence is incomplete; add the real trade-offs (cost, complexity, lock-in, learning curve, migration effort).
- **Deciders** and **Date**: use the names the user gives and today's date. Never invent decider names; if they are unknown, ask.

## 4. Status lifecycle

- 🔴 **R13.** Valid statuses, exactly as written: `Proposed`, `Accepted`, `Deprecated`, `Superseded by ADR-NNNN`.
- 🔴 **R14.** An `Accepted` ADR is immutable. Never change its Context, Decision or Consequences. Only typo and broken-link fixes are allowed in place. To change or reverse a decision, write a new ADR that supersedes it.
- 🔴 **R15.** Superseding links both ways. In the same PR:
  1. New ADR: add `- Supersedes: ADR-NNNN` to its header and explain in *Context* what changed since the old decision.
  2. Old ADR: change only its `Status:` line to `Superseded by ADR-MMMM`. Nothing else.
  3. Update the index.
- 🟡 **R16.** Never delete Deprecated or Superseded ADRs.

## 5. Authoring process

- 🟡 **R17.** Write the ADR before implementing. When asked to implement something that requires an ADR, draft the ADR first.
- 🟡 **R18.** Open the ADR in a PR with status `Proposed`. Reviewers debate in PR comments. Change the status to `Accepted` as part of merging.
- 🟡 **R19.** Accepted ADRs are announced in the team channel. You cannot announce; add it as an unchecked item in the PR description.
- 🟢 **R20.** `adr-tools`, `log4brains` or `adr-manager` may be used to scaffold and render.

## 6. Review and scope

- 🔴 **R21.** ADRs go through PR review like code, with at least one technical approver.
- 🟡 **R22.** ADRs affecting more than one team are also reviewed by the architecture guild.
- 🟡 **R23.** Project decisions live in the project repository; organization-wide decisions ("We standardize on .NET 8") live in the central architecture repository.
- 🟡 **R24.** A project ADR may override an organization-wide ADR only when its *Context* justifies it and links to the organization ADR.

## 7. Review checklist

- [ ] File in `docs/adr/`, correctly numbered, kebab-case, number never used before.
- [ ] Header has Status, Date (ISO), Deciders; `Supersedes` when applicable.
- [ ] Context, Decision and Consequences present; Decision is a firm "We ..." statement.
- [ ] Consequences contain at least one real negative.
- [ ] Alternatives considered, with rejection reasons.
- [ ] No Accepted ADR has had its content changed; supersession links both ways.
- [ ] Index updated.

## 8. Anti-patterns to reject

- "We will use MongoDB." with no context, alternatives or consequences.
- Consequences that read like marketing: "Fast. Scalable. Cloud-native."
- Editing an Accepted ADR to change the decision.
- Retroactive ADRs written long after the fact; acceptable as a last resort, but say so in *Context* and treat it as a signal that decisions are not being recorded up front.

## 9. Pivot.Framework decisions that require an ADR (R1 applied)

In a service built on Pivot.Framework, these choices are ADR-worthy because the framework offers alternatives:

- Persistence provider: SQL Server (default) vs PostgreSQL (`Pivot.Framework.Infrastructure.Persistence.PostgreSQL`); read/write context split.
- Read store: EF Core read models vs MongoDB (`Pivot.Framework.Infrastructure.ReadStore.MongoDB`).
- Transport: RabbitMQ vs in-process publisher; exchange/routing-key design and topology (quorum queues, DLQ).
- Outbox drain mode: `BackgroundPolling` vs `ImmediateAfterRequest`, polling interval, retry/dead-letter policy.
- Enabling the event store (`includeEventStore: true`), projection rebuild/versioning strategy, event upcasting.
- Using sagas (`ISagaOrchestrator`) vs choreography through integration events.
- Authentication topology: Keycloak realm/client layout, audience, Redis token caching and revocation, Blazor Server vs BFF, Hangfire dashboard access.
- API style and versioning: REST (`Containers.API`, `AddPivotApiVersioning` readers) vs gRPC (`Containers.Grpc`).
- Any deviation from the framework (bypassing `UnitOfWork`, custom exception mapping, a second transaction owner) — recorded as a waiver/deviation ADR.

In the **Pivot.Framework repository** itself, write an ADR for: new packages, changes to persisted schemas (outbox, event history, inbox, saga tables) or the RabbitMQ wire format, changes to `Result`/`ResultExceptionType` semantics or HTTP/gRPC status mapping, and new third-party dependencies.

## 10. Worked example

Create `docs/adr/0002-use-client-supplied-idempotency-keys.md`:

```markdown
# ADR-0002: Use client-supplied idempotency keys for payment creation

- Status: Accepted
- Date: 2026-09-29
- Deciders: @alice, @bob

## Context
Clients legitimately retry payment requests (timeouts, crashes, double-taps). Without deduplication, retries
cause duplicate charges. Pivot.Framework offers an inbox-backed `IdempotentCommandBehavior` for commands that
implement `IIdempotentCommand`; it currently supports only commands returning a non-generic `Result`.

## Decision
We require an `Idempotency-Key` header on payment creation, map it to `IIdempotentCommand.IdempotencyKey`, and
enable `AddInboxSupport<PaymentsDbContext>().AddIdempotentCommands()`. The create command returns `Result` and the
client reads the payment through the returned `Location`.

## Consequences
**Positive:** retries never double-charge; uses the framework's inbox table instead of a bespoke store.
**Negative:** clients omitting the header lose protection (mitigated by making it required in the contract); the
command cannot return the new id directly until the framework supports `ICommand<T>` idempotency; inbox rows grow
without a cleanup job.

## Alternatives considered
- No deduplication — rejected: unacceptable duplicate-charge risk.
- Server-generated keys hashing the body — rejected: breaks on immaterial field changes and silently dedups
  requests meant to be distinct.
```
