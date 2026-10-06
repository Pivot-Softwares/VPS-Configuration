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
