---
name: dns-and-mail
description: >-
  Use for any DNS record of pivotsoftwares.com at name.com, managed by hand by the owner, and for the Zoho mail records
  that must keep working: the record register, adding or changing hostnames for the applications, CAA and TTLs, mail
  authentication (MX, SPF, DKIM, DMARC), and checking records from outside.
---

# DNS and mail

`pivotsoftwares.com` is registered and served at name.com. Mail is hosted by Zoho. DNS is managed **by hand** by the
owner (owner decision H, ADR-0001): the agent writes exactly what to configure and checks it from outside. A DNS API
token would be a long-lived credential, so it isn't used.

## Triggers

- An application gets, changes or loses a hostname.
- The VPS's IP address changes (an OVH reinstall keeps it; a new VPS doesn't).
- Mail delivery problems, or a change to Zoho's records.

## Required inputs

- The record register, `docs/reference/dns-records.md`, once it exists: every record, its value, TTL, purpose and the
  decision or work item behind it. It contains no secrets.
- The current records, read from outside with `dig` (or an online DNS lookup) before any change.

## Preflight checks

1. Read the live records first; never write a change from memory.
2. Mail records (MX, SPF `TXT`, DKIM `TXT` under Zoho's selector, DMARC `TXT` at `_dmarc`) are never removed or
   overwritten by an application change.

## Actions

1. **Register before changing:** update `docs/reference/dns-records.md` in the work item's pull request with the exact
   records to add, change or remove.
2. **Give the owner the change as an owner step** (`owner-runbook`): the name.com page, then for each record its type,
   host, value and TTL, exactly as name.com's form asks for them.
3. **Application hostnames:** an `A` record (and `AAAA` only if IPv6 works end to end on the server) per hostname, or a
   `CNAME` to a canonical name when that's simpler to maintain.
4. **CAA:** allow only the certificate authority the proxy uses (`reverse-proxy-caddy`).
5. **TTL:** lower it before a planned change, restore it after.
6. **Mail:** keep Zoho's MX, SPF and DKIM as Zoho specifies them; propose a DMARC policy progression (monitor, then
   quarantine, then reject) with `decision-options`. The server sends no mail unless an ADR decides it does.
7. **Check from outside** after the owner's change and record the output on the work item.

## Prohibited actions

- Asking for name.com or Zoho credentials, or signing in to them.
- Removing or changing a mail record as a side effect of an application change.
- Wildcard records without a decision record.

## Outputs and evidence

- The updated register and the outside check output on the work item.

## Failure behavior

- If a record doesn't resolve as expected after its TTL, check for a typo and for conflicting records before changing
  anything else; propagation is not a reason to make more changes.

## Sources

- [name.com DNS help](https://www.name.com/support/articles/205188538-pointing-your-domain-to-hosting-with-a-records),
  [Zoho Mail DNS configuration](https://www.zoho.com/mail/help/adminconsole/domain-verification.html).
