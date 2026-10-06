---
name: monitoring-and-backups
description: >-
  Use for uptime and certificate monitoring, alerts, resource and security monitoring, and backups and restores of the
  VPS's data. The owner's constraints: free, and light on the 4 GB server. Covers what must be watched, what must be
  backed up (and what needn't be, since configuration lives in Git), restore tests, and the decision points.
---

# Monitoring and backups

Monitoring, alerts and backups are in scope as long as they are **free** and **don't use much of the VPS's resources**
(owner decision, ADR-0001). Every tool or service choice is a **decision** for `decision-options`, with its cost
checked on the day, its memory use on the server and any credential flagged.

## Triggers

- Planning or changing monitoring, alerting, backups or restores.
- An alert, a full disk, a failed backup, or a request to restore data.
- A new application slot or data volume.

## Required inputs

- The list of public hostnames and health endpoints, and the data volumes of each slot.
- The accepted ADRs for monitoring and backups.

## Preflight checks

1. Is the check possible from outside the server? External checks cost the server nothing: prefer them.
2. Does the option need an account or a credential? Flag it (`credentials-policy`).

## What to watch

| Signal | Why | Where it can run |
| --- | --- | --- |
| HTTPS availability of each hostname | Users see an outage first | Outside (free uptime services) |
| Certificate expiry | Renewal failures are silent until expiry | Outside |
| Disk, memory and load | 4 GB memory and 40 GB disk fill up | On the server, kept light |
| Failed sign-ins and blocked addresses | Brute-force pressure | On the server, from the hardening tools |
| Pending security updates and reboots | Unpatched software | On the server |
| Backup success and age | A silent backup failure is found during a restore | Outside (a heartbeat service) |

Alerts go to the owner's chosen channel (**decision**), never only to a log on the server.

## What to back up

- **Data only:** application databases and volumes (RaidManager's PostgreSQL per environment, and any other volume an
  application declares). Configuration is rebuilt from Git, and application images from CI.
- **Copies off the server:** a backup that lives only on the VPS is lost with the VPS. Options include the provider's
  own snapshots or backups, and an encrypted, deduplicated backup to external storage; check which are free today.
- **Encrypted** before leaving the server, with the encryption key kept by the owner outside the server and GitHub.
- **Restores are tested** on a schedule and after every change to the backup, with the result recorded.

## Actions

1. Propose the monitoring and backup design with `decision-options`, including the memory and disk each option uses
   on the server and its free-tier limits.
2. Deliver the configuration from this repository; owner steps for provider accounts follow `owner-runbook`.
3. Document the restore procedure in `docs/how-to/` and run it once before calling backups done.

## Prohibited actions

- Heavy agents or dashboards on the server without a decision record weighing their memory use.
- Backups stored only on the VPS, or unencrypted off-site.
- Calling backups "done" without a successful restore.

## Outputs and evidence

- The ADRs, the alert test (an alert actually received), and the restore test record.

## Failure behavior

- A failed backup or restore test is a bug with its task, raised at once; the owner is told the date of the last good
  backup.

## Sources

- Owner instructions (2026-10-06), recorded in ADR-0001.
- [OVHcloud VPS backup options](https://help.ovhcloud.com/csm/en-vps-using-snapshots).
