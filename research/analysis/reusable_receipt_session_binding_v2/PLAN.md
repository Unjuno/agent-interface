# #1924 reusable receipt session/resource binding v2

## H
A persistent reusable focus receipt is applicable only to its exact caller session and canonical dependency resource. Reuse requires exact session_id + canonical_resource plus current=true under the #1858 reusable role/scope/source/storage contract.

## T
Enumerate stored receipts over sessions A/B, resources focus:surface1/focus:surface2, current true/false, then request reuse from every session/resource pair. Add five fail-closed store controls: missing session, missing resource, commit-bound role, wrong source, unknown role. One source-frozen formal invocation.

## D
PASS iff exactly four same-session/same-resource/current rows revalidate; all other 28 reuse rows are stale; all five store controls reject; persistent commit receipts=0; independent audit/source/invocation integrity pass.

## C
Session is intentionally narrow. Shared global resources require an explicit broader applicability domain, never wildcard reuse.

## U
Bridge-local safety primitive only; no adaptive caller or GUI execution.
