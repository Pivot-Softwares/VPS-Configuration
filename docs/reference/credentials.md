# Credential register

Every credential this repository's automation uses, as `credentials-policy` requires. The register holds no secret
values. Personal access tokens are forbidden.

| Name | Purpose and scope | Location | Owner | Expiry | Rotation | Revocation | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pivot-board-bridge` App private key (`BOARD_APP_PRIVATE_KEY`, client id in `BOARD_APP_CLIENT_ID`) | Board bridge and issue-event runs: one-hour installation tokens with Issues write, Pull requests read, organization Projects write and Issue types write on this repository and the organization | Secret of the `board` environment (deployments from `main` only) | Gihed Annabi | Never | None needed; replace on suspicion of a leak | The App's settings page, Private keys | ADR-0001 (A11), `docs/reference/project-automation.md` |
| Delivery template App private key and webhook secret (planned) | The organization App of the delivery template: Project events and repository configuration, including Administration write | On the VPS, by owner exception of 2026-10-07 (#37); protection defined by ADR-0002 | Gihed Annabi | Never | To be defined in ADR-0002 | The App's settings page | #37, #39, ADR-0002 (task #40) |
