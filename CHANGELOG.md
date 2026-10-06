# Changelog

All notable changes to this repository are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Agent skills for the VPS configuration in `.agents/skills/` and `.claude/skills/`: the RaidManager work-management
  skills, the house documentation and pull request skills, and new skills for conventions, board operations, decisions,
  credentials, owner runbooks, hardening, containers, the reverse proxy, deployments, DNS and mail, and monitoring and
  backups.
- The Work Management and Delivery Specification, adopted from RaidManager with this repository's policies.
- ADR-0001: adopt the RaidManager work process, recording the owner's planning decisions of 2026-10-06.
- The board foundation: the board bridge (`board` workflow, `scripts/board_bridge.py`) for the organization Project,
  RaidManager's hierarchy guard and active-sprint gate without the mockup rule, the issue forms, the type and rule
  labels, the Sprint 1 record and the project automation reference.
- The v1.0 release record, the Sprint 1 selection and capacity, and the Project's field, option and iteration ids in
  `vps-board-operations` (#6).
- Board bridge operations `add-iteration` and `set-options`, which add a sprint and replace a single-select field's
  options while keeping the ids of existing options and iterations, and set again any item value a change drops (#8).
- Native issue types: the board bridge's `sync-issue-types` creates the missing organization issue types and sets each
  issue's type from its label, the hierarchy guard flags a type that doesn't match the label with `type-mismatch`, and
  each issue form sets its type (#25).

### Fixed

- The board bridge and the sprint gate no longer treat Project items they can't read as absent: they stop with the
  number of hidden items and how to fix the App's access, and report GitHub errors (#22).
- An iteration title now resolves to the current or a future iteration before a completed one, and a title shared by
  two iterations is refused instead of resolving to either (#8).
