# Work Management and Delivery Specification

Author and owner: Gihed Annabi  
Date: 2026-10-02  
Status: Adopted for RaidManager on 2026-10-02 by
[ADR-0026](https://github.com/AnnabiGihed/RaidManager/blob/main/docs/adr/0026-adopt-the-work-management-specification.md),
with the owner's amendments marked *Amended* and listed in [section 23](#23-amendment-log).
*Amended 2026-10-06 (A12):* Copied unchanged from `AnnabiGihed/RaidManager` and adopted for
`Pivot-Softwares/VPS-Configuration` by [ADR-0001](../adr/0001-adopt-the-raidmanager-work-process.md). Sections 1 to 21
apply as written; issue numbers in them refer to `AnnabiGihed/RaidManager`. Section 22 holds this repository's
policies.

## 1. Purpose and authority

Use this document as the source for AI agent skills, Architecture Decision Records (ADRs), issue templates,
board configuration, and validation automation.
It consolidates the owner's agreed delivery policies and platform mappings.
*Amended 2026-10-02 (A1):* The owner adopted this specification for RaidManager on 2026-10-02. It is the current
operational authority for work management; skills, issue forms, validators and board configuration link to it rather
than restating it. Where a repository control doesn't match it yet, report the difference to the owner instead of
choosing between them.
The minimum sprint count, sprint duration, stabilization sprint, and execution restrictions are project policies.

MUST means mandatory. SHOULD means the default recommendation, with a recorded reason for deviations.
Owner exceptions require an explicit decision recorded on the affected issue or planning record.
Agents MUST NOT infer approval from elapsed time, field changes, or a closed iteration.

## 2. Work-item hierarchy

```text
Epic
└── Feature
    ├── User Story → Task
    ├── Improvement → Task
    ├── Bug → Task
    └── Spike → Task
```

- Only an Epic has no parent.
- Every other item MUST have exactly one parent of the appropriate type.
- Tasks are leaves; each parent may contain multiple appropriate children.
- Spikes are peers of User Stories and can contain Tasks.
- Releases and sprints are planning dimensions, not additional work-item hierarchy levels.
- Epics and Features may span multiple sprints and releases.
- *Amended 2026-10-02 (A2):* Release assignment follows section 15: a Task shares its parent's release, while
  Stories, Improvements, Bugs and Spikes select their release independently of their Feature.
- Parent relationships and prerequisite relationships MUST be represented separately.

## 3. Classification: intent first, then scope

| Type | Select when | Required outcome | Parent |
| --- | --- | --- | --- |
| Epic | A broad product or engineering objective requires several Features. | Measurable objective delivered through Features. | None |
| Feature | A coherent capability requires several independently verifiable outcomes. | Accepted capability delivered through Stories, Improvements, Bugs, or Spikes. | Epic |
| User Story | A user needs a capability that does not exist yet. | Observable user value and acceptance criteria. | Feature |
| Improvement | Existing behavior meets its specification but should become better. | Verifiable enhancement to quality, usability, performance, tooling, documentation, or process. | Feature |
| Bug | Actual behavior contradicts agreed expected behavior. | Restored behavior with reproduction and regression verification. | Feature |
| Spike | An unanswered question prevents an informed decision or reliable plan. | Evidence, findings, and recommendation within a fixed timebox. | Feature |
| Task | A bounded implementation, investigation, or verification step is needed. | Concrete deliverable supporting its parent. | User Story, Improvement, Bug, or Spike |

Classification procedure:

1. Determine whether the intent is new value, enhancement, correction, or investigation.
2. Determine whether the scope is a broad objective, a capability, an outcome, or an execution step.
3. Select the type and establish its valid parent before execution.
4. Split mixed intents into separately verifiable items when appropriate.

A Spike can succeed by proving that no viable solution exists.
Production code is not required; findings MUST answer the research question or explain the remaining uncertainty.
A Task describes how bounded work is performed and verified; its parent describes why it is required.

## 4. Work-item contracts

Every issue MUST contain its type, parent, purpose, scope, completion conditions, dependencies,
and verification requirements.
An assignee and sprint assignment are required before execution.
Release assignment is required for work selected into release scope.
Owner decisions and completion evidence MUST be linked or recorded on the affected item.

| Type | Additional required content |
| --- | --- |
| Epic | Objective and success measures. |
| Feature | Capability boundaries and expected outcomes. |
| User Story | User, need, benefit, acceptance criteria, and Story Points before sprint selection. |
| Improvement | Current situation, desired enhancement, and verification method. |
| Bug | Expected behavior, actual behavior, reproduction steps, and affected environment. |
| Spike | Research question, timebox, exit criteria, and findings or decision deliverable. |
| Task | Bounded deliverable, execution scope, Delivery Stage, and verification method. |

Parent acceptance criteria MUST describe an outcome.
Closing every child is necessary for parent closure but is not sufficient acceptance evidence.

## 5. Three backlogs

| Backlog | Contents | Purpose |
| --- | --- | --- |
| Product backlog | All outstanding product and engineering work. | Prioritize overall work. |
| Release backlog | Outstanding work selected for one release, including stabilization. | Track remaining release scope. |
| Sprint backlog | Sprint Goal, selected outcomes, child Tasks, and execution plan. | Track the selected sprint's work. |

For planned release work, select from Product backlog to Release backlog to Sprint backlog.
These are views of the same items, not duplicated issues.
Product backlog items may have no release or sprint yet.
Future sprint backlogs can be prepared before their start dates, but execution cannot begin.
Completed and canceled work remains available as history.
Outstanding backlog views exclude completed and canceled work; progress views retain them with distinct outcomes.
Backlog planning does not itself authorize execution.

## 6. Releases

Every planned release MUST have:

- Identifier or version.
- Goal and acceptance criteria.
- Agreed scope.
- Target release date.
- At least two sprints, including a final stabilization sprint.

The date is a target, not a guarantee.
Scope and target-date changes require a recorded owner decision and reason.
A release is a grouping of deliverable scope, not merely a count of elapsed sprints.

| Release state | Meaning |
| --- | --- |
| Planned | Goal, initial scope, and target date exist. |
| In Progress | Delivery work is underway. |
| Stabilizing | Final quality work and release validation are underway. |
| Ready | Acceptance criteria and release checks pass. |
| Released | Approved version published or deployed to its intended destination, with evidence. |

Close the release only after delivery evidence is recorded.
Ending its sprints or completing its issue count MUST NOT automatically close it.
An urgent hotfix may receive an explicit owner exception to the two-sprint minimum or separate stabilization sprint.
It still requires an active sprint, applicable quality checks, and release approval.

## 7. Sprints

A sprint MUST last one or two weeks and have a start date, end date, Sprint Goal, selected work,
capacity forecast, and recorded outcome.
Use a consistent duration where possible.
Record the timezone and exact start/end boundary convention.
For automation, use an inclusive start and exclusive end timestamp: start <= now < end.
If the platform stores inclusive calendar end dates, convert to the next local midnight for the exclusive boundary.

| Sprint state | Meaning |
| --- | --- |
| Planned | Not started. |
| Active | Started, not ended, and not canceled. |
| Ended | Scheduled end reached. |
| Canceled | Owner cancellation and reason recorded. |

Sprints contain Stories, Improvements, Bugs, and Spikes together with their Tasks.
Epics and Features may span multiple sprints.
A sprint MUST end at its scheduled boundary even when work remains unfinished.
Do not extend it merely to finish its scope.
Record goal achievement, completed work, unfinished work, and replanning decisions separately.
Unfinished work remains open and MUST NOT automatically carry into the next sprint.
Preserve historical sprint membership when explicitly rescheduling work.
A sprint can achieve its goal without finishing every originally selected item.

## 8. Active-sprint execution gate

No Task, User Story, Improvement, Bug, or Spike may be executed outside an active sprint.
This applies before starting AND before resuming work.
Epics and Features are executed through eligible child items.

The agent MUST verify:

1. Valid hierarchy and issue contract.
2. Assigned sprint with start <= now < end, and no cancellation.
3. Task and parent outcome have matching sprint assignments.
4. Applicable release assignments are consistent.
5. Assignee and Delivery Stage exist before execution.
6. Prerequisites are satisfied before dependent work starts.
7. Item is neither canceled nor already completed.

If a condition fails, stop execution and report the violated rule and required correction.
Do not mutate dates, assign an arbitrary sprint, or move work to bypass the gate.
When the sprint ends, preserve a safe checkpoint and do not begin another execution action.
Unfinished work requires explicit selection into a new active sprint before resuming.

Execution includes implementation, experiments, proofs of concept, refactoring, cleanup,
deliverable testing, and producing assigned analysis or documentation deliverables.
Planning outside an active sprint is allowed: issue creation, classification, scope refinement,
estimation, prioritization, dependency identification, owner decisions, and preparing future backlogs.
Producing a functional specification, architecture design, ADR, or research deliverable as assigned work is execution.
Administrative recording of sprint outcomes and evidence already obtained is allowed after the sprint ends.
*Amended 2026-10-02 (A5):* Merging a pull request completes its delivery and is execution. A pull request not merged
when its sprint ends waits until its Task is selected into a new active sprint.

## 9. Story Points and capacity

Stories MUST receive an estimate before sprint selection.
Use 1, 2, 3, 5, 8, 13.
Points express relative effort, complexity, and uncertainty, not hours or individual productivity.
Estimate the complete Story, including its required verification.
Split Stories that cannot reasonably finish in one sprint.

- Count the Story estimate once, never both parent and child estimates.
- Use points actually completed in previous sprints to forecast capacity.
- Adjust forecasts for availability and other planned work.
- Account explicitly for Bugs, Improvements, Spikes, and stabilization even when they have no points.
- Timebox Spikes; do not treat their uncertainty as unlimited capacity.
- Use conservative assumptions until historical data exists, and record those assumptions.
- Award no completed Story Points for partial Stories or canceled work.
- Preserve the original estimate and sprint history; do not reestimate merely to inflate completed points.

Capacity describes an amount of work, not a fixed number of Stories.
Keep point-based forecasting separate from time-based capacity reservations rather than adding unlike units.

## 10. Readiness and dependencies

Before sprint selection, verify clear criteria, valid hierarchy, estimate or timebox where required,
necessary inputs/access, capacity fit, goal alignment, and achievable dependencies.

Every prerequisite MUST be either completed and available or selected into the same sprint.
Do not select an item that depends on unfinished work outside the sprint.
Same-sprint dependencies MUST have a realistic order and recorded delivery risk.
Dependent execution waits for the prerequisite's completion evidence.
Apply this rule to Tasks as well as their parents.
Substantial or uncertain prerequisites SHOULD be completed in an earlier sprint.
Reject dependency cycles.
Canceled prerequisites are not satisfied unless an owner decision establishes that they are no longer required.

Ready means ready for the assigned stage, not that every later stage is already complete.
For example, an Architecture Analysis Task needs sufficient inputs, not an already completed architecture design.
Changes during an active sprint MUST preserve the goal and satisfy capacity and dependency rules.

## 11. Status and Delivery Stage

Keep lifecycle Status separate from Delivery Stage.
Status answers whether work is waiting, underway, blocked, under review, or completed.
Delivery Stage answers what activity is taking place.
For example: In Progress / Functional Analysis, or Blocked / Testing.

| Status | Meaning |
| --- | --- |
| Backlog | Captured, not ready for execution. |
| Ready | Defined and eligible for selection; not permission to execute outside an active sprint. |
| In Progress | Execution started within an active sprint. |
| In Review | Deliverable awaits review or acceptance. |
| Blocked | Cannot continue; reason, responsible person, and unblock condition recorded. |
| Done | Criteria satisfied and required evidence recorded. |
| Canceled | *Amended 2026-10-02 (A3):* Explicit non-delivery outcome, closed with its recorded reason; never Done. |

Cancellation is an explicit non-delivery outcome, not Done.
Store a cancellation reason and exclude canceled work from delivery totals.
An unfinished item may remain In Progress after its sprint ends, but its execution is paused by the sprint gate.
Return it to Ready only when that accurately reflects its remaining state; never discard history to tidy the board.

| Delivery Stage | Purpose | Expected evidence |
| --- | --- | --- |
| Business Analysis | Establish problem, users, value, and scope. | Agreed objective and business requirements. |
| Functional Analysis | Define behavior, rules, scenarios, and criteria. | Accepted functional specification. |
| Architecture Analysis | Resolve design, integration, security, and deployment questions. | Design and significant decisions recorded in ADRs. |
| Development | Implement the agreed solution. | Implementation and relevant developer tests. |
| Testing | Verify behavior, integration, and readiness. | Test results and resolved blocking defects. |
| Deployment | Publish or deploy the approved deliverable. | Deployment and smoke-test evidence. |

Stages are not mandatory for every item and are not a rigid waterfall.
Record why a stage is unnecessary where that decision matters.
Testing, security, and refactoring occur throughout development.
Each Task SHOULD have one clear stage; split independently reviewable deliverables across Tasks.
A parent stage indicates current focus; child stages show the precise activity and may overlap.
Blocked work retains its stage.
Changing stage does not establish acceptance or completion.
Development Tasks may finish before deployment; parents close according to their own criteria.
Release closure still requires actual publication or deployment.

## 12. Stabilization

The final sprint of each planned release MUST be a stabilization sprint, included in the two-sprint minimum.
It retains the one-to-two-week duration and all normal sprint execution rules.

Applicable scope includes blocking defects, regressions, identified refactoring/cleanup,
integration and end-to-end validation, documentation, release notes, deployment, and rollback preparation.
Refactoring also occurs throughout delivery; do not postpone ordinary quality work until stabilization.
Use concrete Improvements, Bugs, or Spikes with child Tasks and acceptance criteria.
Avoid new Features during stabilization.
Failed checks remain unresolved work.
Ending stabilization does not authorize release.
If necessary work remains, explicitly revise scope, date, or subsequent sprint plans.

## 13. Completion and closure

| Level | Required condition |
| --- | --- |
| Task | Deliverable complete and required verification evidenced. |
| Story / Improvement / Bug | Own criteria satisfied, checks passed, all Tasks closed, at least one completed. |
| Spike | Exit criteria satisfied, findings recorded, all Tasks closed, at least one completed. |
| Feature / Epic | Own criteria satisfied, all children closed, at least one completed child. |
| Sprint | Scheduled end reached and outcome recorded; unfinished work remains open. |
| Release | Scope accepted, checks passed, owner approval recorded, approved version delivered with evidence. |

*Amended 2026-10-02 (A4):* Closing and reopening an item always sets its Status deliberately:

- Completed: verify the acceptance evidence, close the item as completed, and set Status to Done.
- Canceled: record the reason, close the item as not planned, and set Status to Canceled.
- Reopened: reassess the remaining work and set Status to Backlog, Ready, In Progress, In Review, or Blocked
  according to the evidence. Remove Done or Canceled, record the reason, and verify sprint eligibility before
  execution resumes.
- Validation flags any mismatch between an item's closure reason and its Status.

Canceled children require an explanation of their effect on parent scope.
All children closed does not override unmet parent criteria.
Removing release scope requires an owner decision.
Dates and iteration completion MUST NOT automatically mark work Done.
Repository build, testing, coverage, documentation, review, and other quality gates remain applicable.
No release publication or deployment without the required owner authorization.

## 14. Shared planning records and fields

Work items need stable identifiers and fields for type, parent, Status, Delivery Stage, priority,
assignee, sprint, release, estimates/timeboxes, dependencies, criteria, evidence, and cancellation outcome.
Blocked items also need a reason, responsible person, and unblock condition.
Do not store credentials in work items.

Maintain sprint planning records containing goal, dates/timezone, state, capacity assumptions,
selected scope, outcome, and assignment history.
Maintain release planning records containing version, goal, criteria, target date, scope decisions,
sprint sequence, stabilization plan, readiness evidence, approval, and actual delivery date.
These records do not add new types to the execution hierarchy.

## 15. GitHub Projects mapping

Use native sub-issues for parents and the existing type labels as the classification source of truth.
Exactly one label: type:epic, type:feature, type:story, type:improvement, type:bug, type:spike, type:task.
If native issue types are also configured, validate agreement rather than maintaining conflicting classifications.

| Specification | GitHub mapping |
| --- | --- |
| Hierarchy | Native parent/sub-issue relationships. |
| Status | Project single-select Status with the seven values in section 11 (*amended* A3). |
| Delivery Stage | Custom single-select field with the six stage values. |
| Sprint | Iteration field named Sprint, with start dates and one/two-week duration. |
| Release | Repository milestone, target date as due date; description links to release record. |
| Story Points | Custom number field. |
| Priority | Custom single-select field with documented ordering. |
| Dependencies | Supported dependency relationships plus explicit linked prerequisites. |
| Cancellation | Issue closed as not planned; preserve reason and set Project Status to Canceled (*amended* A3). |
| Evidence | Issue descriptions/comments and linked pull requests (PRs). |

Assign selected outcome items and their Tasks to matching sprints and applicable release milestones.
Do not force multi-release Epics or Features into one milestone.

*Amended 2026-10-02 (A2):* Release milestones follow these rules at each level:

- A Task MUST share its parent Story, Improvement, Bug, or Spike's release milestone.
- Stories, Improvements, Bugs, and Spikes select their release independently of their Feature.
- Features and Epics spanning releases MUST NOT be forced into one milestone; they have no release milestone rather
  than an unrelated one.
- A Feature or Epic may have a milestone only when its entire delivery scope belongs to that release.
- A release view shows the selected items and provides their parent context without assigning those parents to the
  release.

Milestones are repository-scoped; multi-repository releases need a shared release identifier and planning record.
Preserve sprint assignment history before changing an unfinished item's current iteration.
Do not rely on a generic issue-closed workflow that marks canceled issues Done.
*Amended 2026-10-02 (A4):* Disable the built-in Item closed and Item reopened workflows; closing and reopening set
Status as section 13 describes.
An iteration field does not store a Sprint Goal, enforce execution windows, or enforce dependencies.
Use linked planning records and validation automation for those controls.

## 16. Azure DevOps mapping

Use an inherited Agile process where the deployment supports the inheritance model.
Confirm permissions and model compatibility before configuring a project.
This is a mapping for future use, not a decision to migrate RaidManager from GitHub.

| Specification | Azure DevOps mapping |
| --- | --- |
| Epic / Feature / Story / Task | Corresponding work item types in the Agile process. |
| Improvement / Spike | Custom work item types placed at the same requirement backlog level as User Story. |
| Bug | Configure Bugs at the requirement level, not the Task level. |
| Hierarchy | Parent/Child links; validation enforces the exact allowed types. |
| Status | Workflow State with categories mapped below. |
| Delivery Stage | Custom picklist field on the relevant work item types. |
| Sprint | Team-selected Iteration Path with dates; separate linked planning record for goal and state. |
| Release | Custom Release identifier field plus release planning record; optional release/sprint iteration tree. |
| Story Points | Native Agile Story Points field on User Stories. |
| Dependencies | Predecessor/Successor links and explicit prerequisite descriptions. |
| Cancellation | Removed-category state, with recorded reason. |
| Evidence | Acceptance Criteria, custom fields where needed, history, linked PRs, and test results. |

Workflow category mapping:

| State | Category |
| --- | --- |
| Backlog | Proposed |
| Ready | Proposed |
| In Progress | In Progress |
| In Review | In Progress |
| Blocked | In Progress |
| Done | Completed |
| Canceled | Removed |

Configure board columns to match states for every included work item type.
Keep the Delivery Stage as a separate field rather than creating a state for every stage/status combination.
System processes are not edited directly; use supported inherited-process customization.
Native backlog levels and fields do not enforce every cross-item hierarchy or dependency rule.
Preserve assignment history when changing Iteration Path.
If release identifiers are duplicated in iteration names, validate that they match the Release field.
Do not confuse Azure Pipelines deployment releases with the product release planning record.

## 17. Required views

| View | Selection and purpose |
| --- | --- |
| Product backlog | All outstanding work by priority and hierarchy. |
| Release backlog | Outstanding items in the selected release. |
| Release progress | All release items with cancellations separated from completed delivery. |
| Sprint planning | Ready candidates, estimates, stages, prerequisites, and capacity assumptions. |
| Sprint backlog | Selected sprint items, including completed items, grouped by Status. |
| Current sprint | Active sprint execution progress. |
| Future sprints | Prepared upcoming sprint backlogs. |
| Delivery stages | Group by Delivery Stage and display Status. |
| Stabilization | Final release sprint quality work. |
| Blocked work | Blocking reasons and prerequisites. |
| Scheduling violations | Execution without active sprint or inconsistent assignments. |
| Roadmap | Feature/Epic progress and delivery forecasts. |

Implement as Project views on GitHub and appropriate backlogs, boards, queries, and dashboards on Azure DevOps.
Scheduling violations normally require a validator-maintained label/field or report;
ordinary board filtering cannot evaluate every cross-item and date-dependent condition.

## 18. Agent workflow and validation

Before execution, read repository conventions and validate issue contracts, hierarchy,
active sprint, matching assignments, readiness, dependencies, and authorization.
Implement through linked Tasks using the repository's branch and PR rules.
Before completion, validate criteria, run applicable checks, record evidence, and independently validate parents.

Agents MUST NOT invent owner decisions, silently change dates/scope, execute future sprint work,
automatically carry unfinished work, count partial/canceled work as complete, or publish without authorization.
If required information is unavailable, report it as unknown and do not claim eligibility.

Validators MUST detect invalid parents/types, missing contracts, unestimated selected Stories,
execution outside active sprints, inconsistent assignments, unavailable prerequisites, dependency cycles,
premature closure, and release closure without evidence.
Run date-sensitive checks on a schedule and before agent execution, not only when an item changes.
Check relationships again when prerequisites or sprint assignments change.
Administrative automation may record findings; it MUST NOT invent approvals or silently reschedule work.
Board visibility does not equal policy enforcement.

## 19. Skill decomposition

| Skill | Responsibility |
| --- | --- |
| Classification and hierarchy | Select types, link parents, validate contracts. |
| Backlog refinement | Define scope, criteria, estimates, priority, and dependencies. |
| Release planning | Define goal, scope, dates, milestones, and sprint sequence. |
| Sprint planning and eligibility | Capacity, readiness, dates, dependencies, and active-sprint gate. |
| Task execution and completion | Implementation workflow, stages, evidence, and closure. |
| Sprint review and carryover | Record outcomes and explicitly replan unfinished work. |
| Stabilization and release closure | Quality work, readiness, authorization, and delivery. |
| Board configuration and validation | Platform mappings, views, automation, and consistency. |

Each skill MUST declare triggers, required inputs, preflight checks, actions, prohibited actions,
outputs/evidence, failure behavior, and its source decision references.
Keep shared rules in one authoritative specification and link them rather than allowing conflicting copies.
For RaidManager, mirror skill changes in .agents/skills and .claude/skills in the same commit.

## 20. Adoption checklist

- Record owner-approved process decisions in ADRs.
- Align skills, templates, validators, and board configuration in reviewable changes.
- Map existing To Do to Backlog or Ready by readiness, not blindly.
- Preserve In Progress and Done after checking actual evidence.
- *Amended 2026-10-02 (A6):* Map an item to Ready only when the evidence satisfies every applicable requirement;
  otherwise map it to Backlog and record what is missing. Preserve In Progress when work genuinely started,
  including completed child work. Mark Done only when the item's own acceptance criteria and child-closure
  requirements are evidenced. Report the changes and their reasons; ask the owner only about unresolved product
  decisions.
- *Amended 2026-10-02 (A7):* Backfill the section 4 contract of open items from their existing descriptions, linked
  decisions, and evidence, preserving their original content and history. Record unresolved information as
  "Unknown: needs clarification"; never invent requirements or acceptance evidence. An incomplete item may remain in
  Backlog but cannot become Ready or enter a sprint until its applicable contract is satisfied. Closed items that
  predate adoption are exempt; a reopened item meets the current contract before execution resumes.
- Populate Delivery Stage where applicable and record unresolved classifications.
- Establish sprint/release records and dates without retroactively inventing completion evidence.
- Test rules with valid and invalid sample items before enforcement.
- Ensure canceled items do not inflate completion or velocity.
- Verify mirrored skills and applicable repository quality gates.
- Publish configuration instructions and document migration decisions.

## 21. Platform references

- [GitHub Project fields](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields)
- [GitHub iteration fields](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-iteration-fields)
- [Azure DevOps process inheritance](https://learn.microsoft.com/en-us/azure/devops/organizations/settings/work/inheritance-process-model?view=azure-devops)
- [Azure DevOps backlog customization](https://learn.microsoft.com/en-us/azure/devops/organizations/settings/work/customize-process-backlogs-boards?view=azure-devops)
- [Azure DevOps workflow customization](https://learn.microsoft.com/en-us/azure/devops/organizations/settings/work/customize-process-workflow?view=azure-devops)
- [Azure DevOps iteration configuration](https://learn.microsoft.com/en-us/azure/devops/organizations/settings/set-iteration-paths-sprints?view=azure-devops)

Platform mappings were checked against official documentation on 2026-10-02.
Recheck platform support when adopting the configuration, especially for Azure DevOps Server process models.

## 22. VPS-Configuration project policies

*Amended 2026-10-06 (A12):* The owner's project policies for VPS-Configuration (section 1). They follow RaidManager's
(its amendment A8) except where marked. Issue references prefixed `RaidManager` are in `AnnabiGihed/RaidManager`.

| Policy | VPS-Configuration decision |
| --- | --- |
| Sprint duration | Two weeks, every sprint, as in RaidManager. |
| Timezone and boundaries | Europe/Brussels; each sprint starts and ends at local midnight, start inclusive and end exclusive. |
| Sprint 1 | 2026-10-06 00:00 to 2026-10-20 00:00 Europe/Brussels (owner decision, 2026-10-06, ADR-0001). |
| Planning records | Repository files: `docs/planning/sprints/sprint-NN.md` and `docs/planning/releases/<version>.md`, changed through pull requests. A release milestone's description links its record. |
| Automation access | *Amended 2026-10-06 (A11).* No personal token. Workflows enforce what the built-in `GITHUB_TOKEN` can read (issues, labels, milestones, dependencies, pull requests). The Project belongs to the `Pivot-Softwares` organization, and its fields are read and written by the board bridge workflow with the `pivot-board-bridge` GitHub App, whose private key is the only automation secret, in the `board` environment limited to `main`. The agent works from cloud sessions, which can't use a local `gh` login. |
| Deployment status | As RaidManager's A9 and A10: each deployment workflow labels what it delivered with the built-in token (`deployed:<environment>`, `deploy-failed:<environment>`, and the release milestone line). Nobody sets these labels by hand. |
| Story Points | Agents estimate and record the rationale on the issue; the owner may change an estimate. |
| Penpot mockup tasks | Not applicable: this repository has no user interface. |
| First release target date | Unknown: needs owner decision. |

## 23. Amendment log

| Id | Date | Amendment | Decision record |
| --- | --- | --- | --- |
| A1 | 2026-10-02 | Adopted as the current authority. | #323, ADR-0026 |
| A2 | 2026-10-02 | Release milestones per hierarchy level (sections 2 and 15). | #323 decision 2 |
| A3 | 2026-10-02 | Seventh Status value, Canceled (sections 11 and 15). | #323 decision 6 |
| A4 | 2026-10-02 | Closing and reopening set Status deliberately; built-in close and reopen workflows disabled (sections 13 and 15). | #323 decision 7 |
| A5 | 2026-10-02 | Merging a pull request is execution (section 8). | #323 decision 12 |
| A6 | 2026-10-02 | Status mapping of existing items (section 20). | #323 decision 4 |
| A7 | 2026-10-02 | Contract backfill of existing items (section 20). | #323 decision 11 |
| A8 | 2026-10-02 | RaidManager project policies (section 22). | #323 decisions 1, 3, 5, 10, 13, 14 |
| A9 | 2026-10-03 | Deployment status labels per environment (section 22). | #392 owner decisions 2026-10-03 |
| A10 | 2026-10-04 | A merge that changes nothing deployed skips the deployment and still records its items (section 22). | #491 owner decisions 2026-10-04 |
| A11 | 2026-10-06 | VPS-Configuration: Project fields through the board bridge GitHub App (section 22). | ADR-0001, owner decisions A and F on 2026-10-06 |
| A12 | 2026-10-06 | Adopted for VPS-Configuration, with its own project policies (header and section 22). | ADR-0001 |
