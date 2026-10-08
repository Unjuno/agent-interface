# Issue #6530 OrbStack allocation A01 — scoped formal result

**Disposition: `METHOD_PASS_SCOPED`.** Candidate ran once and exited 0; the separate raw-only auditor ran once and exited 0 with `PASS`, 8 rows, and no errors. Scientific retries: 0. The predecessor WSLc environment STOP remains unchanged with formal candidate/auditor/container counts 0/0/0.

## Execution and provenance

- Allocation `TEMPORAL-EFFECT-IDENTITY-6530-ORBSTACK-A01-20261002`; source freeze commit `6edf8c2ac`; base main `aec152dca5d9a28d916761421a74c703600df683`.
- OrbStack Ubuntu 24.04 arm64 VM `agent-interface-6576-tailid-parity-a03-20261002` (ID `01M3Y3Z0A534XSFW13KW95E98Y`), using its private VM-local Docker Engine. No container was running before setup. Existing containers were not changed.
- Pinned image `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, linux/arm64, Python 3.12.15; no pull. TZDB 2026c, `tzdata.zi` SHA-256 `af5c1d3bebe136d372c131bb1a45725f955a8cc2a5ae2fc5a31d3b372e145f49`, New York TZif SHA-256 `e9ed07d7bee0c76a9d442d091ef1f01668fee7c4f26014c0a868b19fe6c18a95`.
- VM cgroup inventory: CPU `200000 100000`, memory `4294967296`, swap `0`. Both Docker containers were inspected before start: network `none`, read-only root, 1 CPU, memory 2 GiB, memory-swap 2 GiB (zero container swap), source/input read-only, and separate output mounts. Configuration is not a claim about measured resource enforcement.
- Candidate container `905f490a11a5e050786adc047910a89a47134165c12b3d7450bd4ba56a0867fa`, started `2026-10-02T14:19:04.045342756Z`, finished `2026-10-02T14:19:04.238188241Z`.
- Auditor container `d7e30f1c2b530fd181b78d56e9332f319820be1e2a127242143364e00b4c3b8c`, started `2026-10-02T14:19:21.740848976Z`, finished `2026-10-02T14:19:21.872006245Z`.
- VM-side candidate raw SHA-256 `d76ad7910e11b7e430eb3081b4fee4af39fc07faf9957d2582d2b92a23e932eb`; VM-side audit JSON SHA-256 `a30fbb4d709d4e4e621833e6726bc0677faf163904d305e7558d676cc90fc2c6`. Both match the separately pulled, locally stored copies. The full VM-side source/input/output hash comparison is retained in `VM_SHA256SUMS.md`.
- Before either container was started, one auditor `docker create` command was rejected because the command line contained a malformed digest (`invalid checksum digest length`). It created no container and invoked no candidate/auditor code. The correct frozen digest was rechecked; a valid auditor container was created and both final configurations were inspected before the candidate start. This command typo is retained as setup history, not treated as a scientific failure or process retry.

## Frozen-case results

| Case | Display baseline | Offset baseline | Typed result |
|---|---:|---:|---|
| Ordinary unique local time | accept | accept | `MATCH`, 2026-03-07 09:00 New York → 14:00Z |
| Fold, first occurrence | accept | accept | `MATCH`, 01:30 → 05:30Z |
| Fold, second occurrence | accept | accept | `MATCH`, 01:30 → 06:30Z |
| Fold without disambiguation | accept | accept | `AMBIGUOUS_UNRESOLVED`, both instants retained |
| Spring-forward gap | accept | accept | `NONEXISTENT_LOCAL_TIME` |
| Daily local-time recurrence | accept | accept | `WRONG_RECURRENCE`; expected 14:00Z, 13:00Z, 13:00Z over March 7–9 |
| No saved event | accept | reject | `NO_EFFECT` |
| Duplicate saved effect | accept | accept | `DUPLICATE_EFFECT` |

The frozen discriminator was met: typed comparison rejected the planted recurrence error that both simpler baselines accepted, and it did not invent a unique instant for the unresolved fold. The independent auditor matched all eight independently authored truth rows (`errors=[]`). Thus the scoped finite method gate passes.

## Scope and limits

This tests only the authored temporal-effect schema and the pinned New York 2026c rules. It is not an application/calendar GUI test, does not verify any real persisted event, and gives no claim about other zones, calendar products, floating/all-day events, future rule changes, user intent, or safety. In particular, the passing synthetic oracle does not grant permission to create or edit a real calendar event.

The immutable predecessor source freeze and WSLc pre-start STOP remain at `research/analysis/temporal_effect_identity_6530_t0/` and PR #6666; this new runtime-specific allocation is additive.
