---
name: container-runtime
description: >-
  Use for the container runtime on the VPS and every Compose service that runs there: installing and configuring the
  runtime, container hardening, networks, volumes, resource limits within 4 GB of memory, logging, image sources and
  pinning, updates and clean-up. Applies to this repository's shared services and to the application slots.
---

# Container runtime

All applications run as containers behind the shared proxy. RaidManager, Delivery Atlas and the website already ship
Docker images or Compose files. The runtime itself (Docker Engine with Compose, rootless mode, or another runtime) is a
**decision** for `decision-options`; these rules apply to whichever is accepted.

## Triggers

- Installing or upgrading the runtime, or changing its daemon configuration.
- Adding, changing or removing a service, network or volume, on the platform side or in an application slot.
- Memory, disk or log pressure on the server.

## Required inputs

- The accepted runtime ADR and the memory budget per slot (the server has 4 GB in total, and RaidManager alone runs
  three environments).
- Each service's image, ports, volumes, environment and health check.

## Preflight checks

1. The service has a memory limit and the sum of all limits leaves room for the system and the proxy.
2. The image comes from a source the owner accepted, pinned by version or digest.

## Actions

1. **Harden every container** unless the service documents why it can't: a non-root user, `read_only: true` with
   `tmpfs` for scratch space, `cap_drop: [ALL]` and only the capabilities it needs back, `no-new-privileges:true`, a
   `pids_limit`, memory and CPU limits, a health check and `restart: unless-stopped`. Delivery Atlas's `compose.yaml`
   is the reference shape.
2. **Networks:** one internal network per application slot, plus the shared proxy network for the services the proxy
   routes to. Databases join only their slot's internal network.
3. **Ports:** no service publishes a host port except the proxy (`reverse-proxy-caddy`). Published ports can bypass a
   host firewall that isn't configured for containers (`vps-hardening`).
4. **Never mount the runtime's socket** into a container; a container with it controls the host.
5. **Volumes:** named volumes for data, listed in the backup plan (`monitoring-and-backups`); no host paths into Git
   checkouts.
6. **Logs:** the runtime's log rotation configured globally, sized for 40 GB of storage.
7. **Images:** built by CI in the application repository, never on the server, unless an ADR decides otherwise. Pull
   access to a private registry needs a credential (`credentials-policy`); public images need none.
8. **Updates and clean-up:** a planned way to apply new base images, and regular removal of unused images, so the disk
   doesn't fill.

## Prohibited actions

- Privileged containers, host network mode, or the runtime's socket inside a container, without an ADR.
- `latest` tags in anything deployed.
- Secrets baked into images or committed in Compose files.
- Adding an always-on service without checking the memory budget.

## Outputs and evidence

- The Compose files or service definitions, the memory budget table in `docs/`, and `docker stats` style evidence
  pasted by the owner after the change.

## Failure behavior

- A service that fails its health check after a deployment is rolled back by the deployment
  (`github-actions-deployment`); report the logs the owner pastes, never debug by loosening the hardening.

## Sources

- [Docker Engine security](https://docs.docker.com/engine/security/),
  [Docker and ufw](https://docs.docker.com/engine/network/packet-filtering-firewalls/).
- `AnnabiGihed/Delivery-Atlas` `compose.yaml`; `AnnabiGihed/RaidManager` `deploy/server/`.
