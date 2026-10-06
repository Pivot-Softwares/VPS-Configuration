---
name: architecture-proposal
description: 'Produce an architecture proposal for a service built on Pivot.Framework from a business analysis: the mandatory document structure (scope, quality attributes, argued decisions, component/deployment model, data and integration design, cross-cutting concerns, footprint, decision index), the Pivot-based mandatory frame, how decisions become Proposed ADRs, the Azure-DevOps-Wiki-compatible C4 diagram set, and publishing the proposal as a downloadable PDF workflow artifact that is never committed. Use when designing or reviewing a system architecture, writing an architecture document, evaluating design options, or turning a business analysis into a technical plan.'
---

An architecture proposal answers one question — **what is the technical design** — on top of analysis someone else has already produced.

## Who owns what (respect this boundary)

The **functional analyst** owns and delivers as input: the business analysis and **domain model**, the **primary business flows**, the **behaviours to specify** (BDD scenarios / acceptance criteria), and the **user stories and their sequence**. **Do not produce these.** Restating them duplicates the analyst's work. If the analysis is missing or ambiguous, say what you need and from whom.

**You** own the technical design: decisions and trade-offs, the component and deployment model, data and integration design, cross-cutting concerns, infrastructure footprint, platform dependencies, and the ADRs. Where the domain model drives a technical decision (aggregate boundaries → transaction scope), **reference** the analyst's model and explain the consequence. Use with `docs-adr`, `docs-diagrams-as-code` and `docs-as-code`.

## Document structure (mandatory sections, in this order)

1. **Scope and inputs** — the capability served and an explicit reference to the functional analysis (document, work item, author, version). Assumptions you had to make, and what changes if each is wrong. Cite — don't restate — the domain model, flows, scenarios and backlog.
2. **Quality attributes** — volume, latency, availability, RTO/RPO, data classification, auditability, regulatory/retention constraints — numbers wherever the analysis gives numbers. Every decision is argued against these.
3. **Architecture decisions** — each as options → trade-offs → recommendation → consequences (positive **and** accepted negatives). Opens with the **architecture pattern choice** (below).
4. **Component and deployment model** — what is actually deployed and how it's wired (rules below).
5. **Data and integration design** — persistence, ownership, the domain-type catalog, external systems, contracts (OpenAPI/AsyncAPI/proto), failure modes (dead-lettering, retries, idempotency).
6. **Cross-cutting concerns** — identity and authorization, observability, resilience, configuration and secrets, and the test strategy at the level of *what is verified where*.
7. **Infrastructure footprint and platform dependencies** — modules, pipelines, platform requests (with lead times).
8. **Decision index** — the ADRs produced, one-line rationale each.

## The mandatory frame (given, not argued)

In RaidManager, accepted ADRs override parts of this frame (Discord instead of Keycloak, no broker yet) — see
`raidmanager-conventions`. Design inside it and do not re-argue it; "follows the house standard" is still not a justification for decisions that *were* yours:

- .NET 10 LTS, Clean Architecture, the house solution structure and feature-first folders (`dotnet-solution-scaffolding`, `dotnet-ddd-cqrs-conventions`).
- **Pivot.Framework** as the foundation of every layer (`pivot-framework`): Domain primitives and `Result`, MediatR dispatch through Pivot's `ICommand`/`IQuery`, `ValidationPipelineBehavior`, `UnitOfWork` with transactional outbox, `ApiController`/middleware or the gRPC interceptors. No hand-rolled equivalents, no third-party replacements for what Pivot provides.
- Persistence: **SQL Server + EF Core, code-first migrations** (`Pivot.Framework.Infrastructure.Persistence.EntityFrameworkCore`).
- Authentication: **Keycloak** through the Pivot authentication packages (`pivot-auth-aspnetcore`, `pivot-auth-blazor`, `pivot-auth-maui`, `pivot-auth-hangfire`).
- Asynchronous integration: **RabbitMQ through Pivot's outbox** (`pivot-messaging-outbox`) — integration events, inbox deduplication, topology with DLQs.
- Scheduling: Hangfire via `Pivot.Framework.Infrastructure.Scheduling`.
- Containerised hosts; CI/CD pipelines + Terraform; SonarCloud gate; OpenTelemetry (`AddPivotObservability`) to the organization's APM.

A genuine need to deviate (e.g. a non-Pivot broker, bypassing the unit of work) is proposed explicitly as a **deviation**, justified, and flagged as requiring human approval.

## Decisions you *do* argue (Pivot gives you options)

Open section 3 with the **architecture pattern**, chosen from what Pivot supports:

| Option | Pivot building blocks | When |
|---|---|---|
| **A. Outbox CQRS** (default) | state-stored aggregates, `UnitOfWork` + outbox, EF/Mongo read models via `ProjectionHandler` | most services |
| **B. CQRS with event history** | A + `includeEventStore: true`, `EventHistory`, `IProjectionRebuilder`/`IProjectionCoordinator`, `IEventUpgrader` | audit trail by event, rebuildable/blue-green projections |
| **C. Orchestrated process** | A or B + `ISagaOrchestrator` sagas with compensation | multi-step, cross-service business transactions |
| **D. Simple CRUD-style aggregates** | `LightweightAggregateRoot`/`Entity` + UoW, no read models | low-complexity reference data |

Full event sourcing (state rebuilt only from events) is **not** provided by Pivot — proposing it is a deviation.

Then argue, as applicable: SQL Server vs PostgreSQL (`…Persistence.PostgreSQL`); read store EF vs MongoDB; outbox drain mode (`BackgroundPolling` vs `ImmediateAfterRequest`) and retry/dead-letter policy; routing and topology; REST (`Containers.API`) vs gRPC (`Containers.Grpc`); API versioning reader; Redis token caching/revocation; Blazor Server vs BFF (`Authentication.API`); saga vs choreography; caching (`ICacheService`, BFF cache).

### Argue every decision — the core of the proposal

For each significant decision, the document **and** its ADR contain: at least two real, named options; pros and cons of each; the decision; **why the chosen option beats each rejected one specifically**; the negative consequences accepted.

> **Decision:** <what we adopt>
> **Options considered:** A <name>, B <name>, C <name>
> **Trade-offs:** A — pros / cons; B — pros / cons; C — pros / cons
> **Why A over B and C:** <the specific reason each rejected option was worse for THIS system — quality attributes, cost, complexity, fit, skills>
> **Consequences:** positive … ; **negative (accepted):** …

A decision listing only the winner is incomplete and goes back.

### Other rules
- **Right-size.** The simplest design that satisfies the analysis and the frame; state what you deliberately left out (event history, sagas, Mongo, extra contexts, caching) and the future condition that would justify it.
- **Every business rule has a home** (an aggregate or policy); otherwise fix the model first.
- **Separate advice from delivery.** Documentation, diagrams and illustrative snippets only — no application code, scaffold or tests.
- **Assumptions are first-class**, each with its impact if wrong.
- **Known framework limitations are design inputs**, not surprises: event-id round-tripping for inbox dedup, `IIdempotentCommand` only on non-generic commands, no distributed lock in the polling drain (see `pivot-framework` "Known defects"). Name the mitigation you rely on.

## Decisions become Proposed ADRs

Each significant decision becomes an ADR in `docs/adr/` per `docs-adr`: `NNNN-kebab-case-title.md`, never-reused numbers, status **`Proposed`** (only a human accepts), Context / Decision / Consequences / Alternatives considered. Typical set: architecture pattern, persistence provider and read store, transport + drain mode, authentication topology, API style and versioning, testing strategy, deployment. Index them in `docs/adr/README.md`. Never mark an ADR `Accepted` yourself, never edit an Accepted ADR (supersede it), never use an ADR to waive a mandatory standard without the waiver process (`docs-standards-governance`).

## The deployment model — what is in it, and what is not

It describes **what runs in a real environment**:
- **No development-time orchestration:** no Aspire AppHost, no Keycloak/SQL Server/PostgreSQL/RabbitMQ/Redis/Mongo containers started by Aspire or Testcontainers. Show the deployed services (e.g. Azure SQL Database, Azure Cache for Redis, the organization's Keycloak and RabbitMQ). A separate, clearly labelled development diagram is allowed.
- **No shared platform components as owned boxes:** application gateway/WAF, hub firewall, a shared RabbitMQ cluster or Keycloak realm server, container registry, log analytics — consumed, not owned; external boundaries at most; excluded from the application's cost model.
- Stay in the organization's approved region and service catalogue. A service outside the catalogue is a **platform onboarding request** with a lead time, not a unilateral design choice — say so explicitly (this applies to RabbitMQ, Keycloak, MongoDB and Redis wherever the platform doesn't already provide them).

### Front-end
**Blazor Server** is the default. **Blazor WebAssembly is not supported by `Pivot.Framework.Authentication.Blazor`** (server-side Redis sessions + HttpOnly cookie) — never propose WASM without naming that consequence and an approved alternative (a BFF on `Pivot.Framework.Authentication.API`). ASP.NET MVC Core for low-interaction flows; MAUI/Blazor Hybrid with `Authentication.Maui` for mobile/desktop.

## Diagrams

Mermaid sources under `docs/diagrams/`, embedded in the document (`docs-diagrams-as-code`):
- **Context** — the system, users, neighbouring systems (Keycloak as external IdP).
- **Container** — only what's deployed: API/gRPC hosts, jobs, UI, data services, broker exchanges, message paths.
- **Sequence** — the primary write path end to end: request → validation behaviour → handler → aggregate → unit of work → outbox → drain → broker → consumer (template in `docs-diagrams-as-code` §12).
- Optional: `erDiagram` with **domain-type annotations on every column** (including Pivot's `Version`, `Audit_*`, `IsDeleted`, outbox/inbox/event-history tables), state diagrams for real lifecycles.

Azure DevOps Wiki's Mermaid: C4 as `flowchart` with the shape conventions — never the `C4Context`/`C4Container` dialect. Commit every source; no rendered image without its source.

## The domain type catalog (section 5)
Strongly typed ids per aggregate (`StronglyTypedGuidId`), value objects with their invariants and `Result<T> Create`, enumerations instead of free strings, translation/money value objects instead of parallel fields — every remaining primitive justified. Integration-event payloads use primitives (they are JSON contracts) — list them with their versioning policy.

## Publishing the PDF (downloadable, never committed)

- **Committed — ONE canonical file:** `docs/explanation/architecture-proposal.md`. No duplicate architecture document; if an older `docs/Architecture/Architecture-<Solution>.md` exists, fold it in and delete it. `docs/index.md` links the proposal.
- **Not committed:** the PDF. `.github/workflows/architecture-proposal-pdf.yml` (or the Azure Pipelines equivalent) triggers on changes to the proposal or `docs/diagrams/**` (PR and default branch), renders with pandoc (Mermaid, TOC, numbered sections) and uploads the artifact `architecture-proposal`, retained 30 days — available on the first push, before merge.
- **Guards:** `.gitignore` contains `docs/explanation/*.pdf`; the workflow fails if a `.pdf` is in the tree.
- **Tell the reader:** the PR states where to download (Actions/Pipeline run → artifact `architecture-proposal`) and the retention.
If the workflow can't run here, commit it and the Markdown anyway and record under Risks that the PDF must be generated by running it.

## Completion criteria
- All eight sections, in order, none empty, none restating the analyst's model, flows, scenarios or backlog.
- The architecture pattern is chosen among Pivot's options A–D (or a flagged deviation), and **every decision** states options, trade-offs, why the winner beats each loser, and accepted negatives — in the document and the ADR.
- Frame respected: Pivot.Framework foundations, SQL Server/EF Core (or an argued PostgreSQL ADR), Keycloak via Pivot auth, RabbitMQ via Pivot outbox; known framework limitations named with mitigations.
- Domain type catalog present; `erDiagram` annotated with domain types.
- Deployment model contains only deployed, owned components; shared platform services are external boundaries; non-catalogue services flagged as onboarding requests.
- Front-end is Blazor Server unless an approved exception is documented with its auth consequence.
- ADRs `Proposed` and indexed; one proposal document; Mermaid sources committed; PDF workflow + `.gitignore` guard present; no `.pdf` committed; no application code, tests or scaffold.
