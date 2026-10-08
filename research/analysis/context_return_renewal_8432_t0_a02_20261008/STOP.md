# Issue #8432 T0 A02 — STOP: raw not retained

**Status:** `STOP_RAW_NOT_RETAINED` — no method result.

The frozen candidate was invoked exactly once in the specified isolated
OrbStack container. It exited 0 and printed:

```text
{"allocation_id":"8432-context-return-method-t0-a02-20261008","episode_count":18,"output":"RAW.json"}
```

The candidate wrote `RAW.json` to `/run`, a container-local tmpfs. The tmpfs
contents disappeared when the container stopped. The one post-run retrieval
attempt failed with:

```text
Error response from daemon: Could not find the file /run/RAW.json in container issue8432-a02-candidate-once
```

No raw bytes were recovered; the stdout episode count is not independently
verified. The candidate invocation is consumed: no rerun, host fallback, raw
reconstruction, or substitute audit was performed. The independent auditor was
not invoked because its required raw input was unavailable.

## Invocation accounting

| Gate | Invocations | Outcome |
|---|---:|---|
| Construction tests before freeze | 1 command | PASS, 18/12/6 design and 6/6 synthetic mutants |
| Frozen candidate | 1 | exit 0; stdout claims 18; raw unavailable after container exit |
| Independent auditor | 0 | not invoked; no raw input |
| Retries / host fallback | 0 | none |

The construction check is not a formal result. `PASS_METHOD_SCOPED`, renewal,
and history-benefit claims are not established.

## Runtime evidence

- Image: `node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`
- Container: `525d70ddc7370c82f4585bad7734e6f96a2c016d39466d7a0671d4e568c0e598`
- Platform: OrbStack Docker Engine, Linux/ARM64.
- Exit: 0; started `2026-10-08T04:48:53.182750154Z`, finished `2026-10-08T04:48:57.227891846Z`.
- Inspected configuration: network `none`, read-only rootfs, user `1000:1000`,
  256 MiB memory, 0.5 CPU, 32 PID limit, all capabilities dropped,
  `no-new-privileges`.
- These inspected settings establish configuration, not independent proof of
  host resource enforcement.
- The exact candidate command used a read-only bind mount for the package and
  `/run` tmpfs for output. The result demonstrates that this output placement
  was not persistent past container exit; it does not establish a scientific
  finding about context-return behavior.

## Frozen provenance

Source identity is recorded in `FREEZE.json`. Candidate, auditor, fixture and
preregistration were not changed after freeze. A01's failure and unresolved
archive-byte identity remain untouched; A01 raw was not used.

`FREEZE.json` records the preregistered target budget of one candidate and one
auditor invocation, not the realized count. The realized formal count is the
table above: candidate 1, auditor 0, retries 0.
