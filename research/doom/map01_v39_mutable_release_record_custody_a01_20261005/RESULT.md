# A01/A02 outcome

## A01 — setup STOP

`STOP_CONTAINER_CLI_IMAGE_PARSE`; no container started and no candidate ran. Docker treated the misplaced `PYTHONDONTWRITEBYTECODE=1` token as the image reference. The exact command/error are in `STOP_A01.txt`. No output was overwritten.

## A02 — mutable-record custody pair

The single container command executed the identical forced fake-Xlib schedule against the exact frozen PR #7805 owner V13 / bridge V2 bytes: baseline once, diagnostic probe once. The per-key post-release query was faulted to unavailable; the subsequent aggregate pointer query was gated after the mutable owner record was appended and before its aggregate reconciliation.

| Case | At gate | After aggregate query | Final bridge held | Disposition |
|---|---|---|---|---|
| Frozen bridge V2 | `verified=false`; one `PHYSICAL_SAMPLE_UNAVAILABLE` release row consumed | Same record becomes verified-empty | `F8` | `FAIL_REPRODUCED_MUTABLE_RECORD_CUSTODY` |
| Diagnostic neutral-state revisit | Same partial row consumed exactly once | Same record becomes verified-empty | empty | `PASS_DIAGNOSTIC_NEUTRAL_STATE_REVISIT_SCOPED` |

Both cases end with owner-held and fake physical key sets empty. Neither emits a `CONFIRMED_PHYSICAL_UP` receipt: the per-key sample was unavailable. The probe adds no duplicate event. The independent raw-only audit recomputed source identities, same-record mutation, receipt classification/identity, cursor position, and final owner/bridge/fake states; 0 mismatches.

The first A02 audit wrapper wrote its deterministic report under `formal_01/` due to a path typo. After correction, `formal_02/audit.json` was generated; `cmp` confirms the two reports are byte-identical. The candidate raw was unchanged and not rerun. A post-run preflight invocation refused the already-existing write-once A02 candidate output as intended. Details are in `AUDIT_WRAPPER_NOTE.txt`.

**Conclusion:** this schedule reproduces stale bridge-held bookkeeping after an in-place aggregate-neutral mutation of a consumed owner record. A diagnostic revisit of the verified-neutral state resolves the stale ledger for this one schedule without fabricating per-key edge evidence. This does not establish the right production concurrency protocol.

Scope is limited to synthetic fake-display mechanics. No X server, physical keyboard, application/game, model, useful task feedback, recovery, threat exposure, latency distribution, safety, or MAP01 attempt ran. Issue #59 remains open.
