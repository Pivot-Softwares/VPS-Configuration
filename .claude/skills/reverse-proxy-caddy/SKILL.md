---
name: reverse-proxy-caddy
description: >-
  Use for the shared reverse proxy in front of every application on the VPS: choosing it, adding or removing a site,
  HTTPS certificates, security headers, redirects, routing to containers, and checking the result from outside. Caddy
  is the proxy RaidManager used on this server; it applies here only once a decision record accepts it.
---

# Shared reverse proxy (Caddy)

One reverse proxy terminates HTTPS for every hostname under `pivotsoftwares.com` and forwards to the application
containers on an internal network. RaidManager ran a shared Caddy on this server (its ADR-0027). The choice for the new
server is still the owner's: propose it with `decision-options` (Caddy, Traefik and nginx with a certificate client are
the usual options) before writing configuration. The rules below hold for whichever proxy is accepted; the Caddy
specifics apply when Caddy is.

## Triggers

- Adding, renaming or removing a hostname or an application.
- Changing TLS, headers, redirects, timeouts, request limits or logging on the proxy.
- A certificate, routing or header problem seen from outside.

## Required inputs

- The accepted proxy ADR, the list of hostnames and the container each one routes to.
- The DNS records for each hostname (`dns-and-mail`), which must resolve to the VPS before a certificate can be issued.

## Preflight checks

1. Each hostname has its DNS record and a CAA record that allows the certificate authority.
2. The proxy is the only container publishing ports 80 and 443; applications publish none (`container-runtime`).

## Actions

1. **Keep the configuration in this repository**, one file per application slot plus a shared part, so each
   application's hostnames are reviewed with its pull request.
2. **Every site gets the shared baseline:** HTTPS only with redirects from HTTP; HSTS once the owner accepts it
   (**decision**: it is hard to undo); security headers (`X-Content-Type-Options`, `Referrer-Policy`, a frame policy,
   and a content security policy agreed with the application); no server version banner; request size and timeout
   limits; access logs with rotation.
3. **Route to containers by name** on the internal proxy network; never to a published host port.
4. **Certificates:** automatic issuance and renewal (ACME). Use the staging authority while testing a new hostname to
   stay within rate limits. A DNS challenge needs a DNS API credential: avoid it (`credentials-policy`) unless the
   owner decides otherwise.
5. **Validate before reload** (`caddy validate` for Caddy) and reload without dropping connections; the deployment
   keeps the previous configuration when validation fails.
6. **Check from outside** after each change: the certificate chain and expiry, the redirect, the headers, and that
   no other port answers.

## Prohibited actions

- Writing proxy configuration before the proxy decision is accepted.
- Publishing an application's port on the host, or routing around the proxy.
- Turning on HSTS preload or long HSTS ages without an owner decision.
- Disabling certificate verification between components to "make it work".

## Outputs and evidence

- The configuration files, the outside check results (certificate, headers, redirects) on the work item.

## Failure behavior

- A failed validation stops the deployment and keeps the running configuration; report the error with its line.
- A failed certificate issuance: check DNS and CAA first, then the authority's rate limits, before changing anything.

## Sources

- [Caddy documentation](https://caddyserver.com/docs/), [Let's Encrypt rate limits](https://letsencrypt.org/docs/rate-limits/).
- `AnnabiGihed/RaidManager` ADR-0027 and `deploy/server/raidmanager.Caddyfile`.
