---
name: vps-hardening
description: >-
  Use for any change to the VPS's operating system security: the installation after the reset, accounts and sudo, SSH,
  the host firewall and the OVH network firewall, brute-force protection, automatic security updates, kernel and
  network settings, time sync, logging and auditing. Gives the baseline every proposal must cover, the checks that
  prove it, and what must go through a decision record.
---

# VPS hardening

Security of the VPS is the owner's first priority. This skill lists what the baseline must cover; it doesn't choose
the tools. Each choice below marked **(decision)** goes through `decision-options` and becomes an ADR before it is
applied. Steps on the server follow `owner-runbook`.

## Triggers

- Planning or changing the reinstallation, an account, SSH, a firewall rule, an update policy, a kernel setting or a
  security tool.
- A finding from monitoring, an external scan or a security advisory that concerns the server.

## Required inputs

- The accepted ADRs, the server facts (OVH VPS, 2 vCores, 4 GB memory, 40 GB storage, IPv4 and possibly IPv6).
- The services that must be reachable: HTTPS for the applications, SSH for administration and deployment.

## Preflight checks

1. The change can't lock the owner out, or the safety net is in place (`owner-runbook`).
2. The change keeps every item of the baseline true, or the pull request says which item changes and why.

## Baseline (every item covered by an ADR, a runbook and a check)

| Area | Baseline | Decision points |
| --- | --- | --- |
| Operating system | A supported LTS release from OVH's images, nothing extra installed. | **(decision)** distribution and version |
| Accounts | No shared accounts. A named admin account with sudo; separate deploy accounts per application with no sudo and no shell beyond what deployment needs; root sign-in disabled. | **(decision)** how deploy accounts are restricted |
| SSH | Keys only (no passwords, no keyboard-interactive), no root sign-in, modern algorithms, allow-list of accounts, idle timeout. | **(decision)** port, key type, whether the OVH KVM console is the only fallback |
| Host firewall | Default deny inbound; allow only HTTPS (and HTTP for certificate challenges and redirects) and SSH; outbound limited if practical. Docker must not bypass it. | **(decision)** tool, and how published container ports are handled |
| Network firewall | The OVH network firewall as a second layer in front of the VPS. | **(decision)** use it or not, and its rules |
| Brute force | Repeated failed sign-ins are blocked. | **(decision)** tool, weighed against memory use |
| Updates | Security updates install automatically; reboots needed by kernel updates happen at a planned time with the applications coming back on their own. | **(decision)** reboot window |
| Kernel and network | Standard hardening settings (no IP forwarding unless containers need it, reverse-path filtering, SYN cookies, no redirects). | none expected |
| Time | Time synchronization on. | none expected |
| Logs | System and SSH logs kept with rotation, sized for 40 GB. | **(decision)** retention, and whether logs leave the server |
| Secrets on disk | Only run-time secrets of the applications, readable only by their accounts (`credentials-policy`). | per application |

## Actions

1. Propose each decision point with `decision-options`, flagging every credential.
2. Prefer configuration delivered from this repository (files and a script or workflow that applies them) over
   commands typed on the server, so a reset can be replayed. Hand-typed steps go in a runbook with their reason.
3. Write the check for each baseline item: a read-only command for the owner, and an outside check where possible
   (open ports, SSH authentication methods, TLS).
4. Record the applied state and its evidence on the work item, and update the baseline document in `docs/` with what
   is now true.

## Prohibited actions

- Enabling password authentication, root sign-in or a service listening publicly that the baseline doesn't list.
- Disabling the firewall or automatic security updates, even to debug.
- Installing an agent, panel or tool on the server without a decision record.
- Running a hardening script from the internet without review.

## Outputs and evidence

- The ADR for each decision, the configuration files or scripts, the runbook, and the check outputs.

## Failure behavior

- If a check fails after a change, report it as a bug under the hardening feature and give the undo step first.

## Sources

- [OVHcloud: secure a VPS](https://help.ovhcloud.com/csm/en-vps-security-tips),
  [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) for the chosen distribution.
- `AnnabiGihed/RaidManager` `deploy/server/provision.sh` (the previous provisioning, to be replaced).
