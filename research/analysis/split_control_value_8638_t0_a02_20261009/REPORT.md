# Issue #8638 T0 A02 result

**Disposition: `PASS_METHOD_SCOPED`.** The frozen finite simulator and independent raw-only auditor agree on all 192 supported rows across 13 cases. All three preregistered A/B pairs showed the expected ranking reversal: the single-controller VOI-C and acquisition-information-minus-cost proxy ranked A above B, while the split-control expected net value ranked A below B. The full raw ledger, audit, invocation receipt, hashes and scope limits are retained in this package.

## Observed pair results

| Pair | A VOI-C | B VOI-C | A split-control net | B split-control net | Direction |
|---|---:|---:|---:|---:|---|
| Reference | 0.350 | 0.200 | -0.028 | 0.175 | Reversed |
| Held-out 1 | 0.320 | 0.180 | 0.000 | 0.158 | Reversed |
| Held-out 2 | 0.310 | 0.200 | -0.047 | 0.144 | Reversed |

For the reference pair, the information-minus-cost proxy ranked A at 0.614 and B at 0.139. It ignores delivery and downstream uptake by construction, so its ranking did not represent realized decision value.

The `positive_but_unconsumed` control had VOI-C +0.380 and split-control net value -0.020 at zero uptake. The rare/high-consequence cue retained positive split value (+0.113); the irrelevant cue was -0.010; an ignored cue was -0.020; and a misleading downstream response was -0.310 despite positive VOI-C (+0.290). `stale_signal` remained `UNKNOWN_STALE`, with no cue-specific VOI or information score and no signal passed to the downstream decision. `out_of_model_unknown` remained `UNKNOWN_SUPPORT` and unscored. All cases retained `authority=NONE`; mandatory gates were unchanged.

## Execution and audit

The candidate ran once and exited 0, writing the full 13-case / 192-row JSON to `raw/candidate_raw.json`. Its emitted SHA-256 matched the file. A separate raw-only auditor ran once and exited 0 with `PASS_METHOD_SCOPED`, zero errors, and the same raw digest. Exact commands, timestamps, source commit, exit codes and digests are in `raw/execution_receipt.json`. The formal execution used the frozen macOS network-deny sandbox; a separate loopback probe was denied with `EPERM`.

Six construction mutations were rejected before freeze. These are construction controls, not six additional formal candidate/auditor runs. A pre-freeze audit formatting defect on exact zero was preserved in the construction record and fixed before the allocation was frozen.

OrbStack was not used. The daemon's read-only container inventory failed on a containerd content-blob `operation not supported` error before any container action. This T0 is a standard-library deterministic finite enumeration and does not require an image/runtime boundary; the native sandbox was therefore the scoped fallback. No container identity, resource enforcement or Docker parity is claimed.

## A01 provenance and custody

A01's one candidate and one auditor invocation produced a method-pass summary in memory, but its complete raw table was not persisted. This artifact-custody STOP remains unchanged; A02 is a fresh allocation and its files do not repair or relabel A01. The A01 branch's actual parent was later found to be `1f81daa690b567a9a049cc75fae8619b2660c343`, while its embedded `base_main` named `437db9f8c8e77e3ad38a61c2e6a42f5cdb06fcb2`. The A01 fixture was self-contained, but that metadata mismatch remains part of A01's provenance record. A02 froze against current main `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`.

## Scope

This result validates accounting only for the frozen synthetic finite model and its declared loss/probability tables. It does not estimate real model or user uptake, establish that repository observations have negative value, test a GUI or application, measure latency or task effect, validate any runtime policy, or establish safety or product benefit. A single-controller VOI-C remains adequate where its downstream policy assumptions hold. Future real-world work needs independent evidence for delivery, use, decision response and loss; this result grants no execution authority.
