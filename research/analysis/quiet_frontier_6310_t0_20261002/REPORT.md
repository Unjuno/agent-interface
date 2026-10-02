# Issue #6310 T0 — predicate-relative quiet-frontier method result

**Outcome:** `PASS_METHOD_SCOPED` under the frozen finite synthetic contract below. This is not a certificate for any real GUI and does not grant action authority.

**Allocation:** `QUIET-FRONTIER-6310-T0-20261002-01`  
**Issue:** https://github.com/Unjuno/agent-interface/issues/6310  
**Main at intake:** `c81e3d8ffebc7cbc2af971dfb7fb2d9b1ba1f7fe`  
**Main at formal preflight:** `ab43adce8141182f6bcfa76df469854b1ae11116` (+1 commit: unrelated #59 X11 event evidence; no dependency on this fixture).  
**Main at publication preflight:** `d23c909f5dad11d6f87f1c3139cbcad52096cc4e` (+1 commit after formal run, unrelated #6061 intermittent-identity measurement; no source/path collision).  
**Runtime:** Arch Linux WSL2, WSL Containers 3.0.1; image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64).

## Frozen hypothesis and exact scope

`FREEZE.md` defines H/T/D/C/U. The finite contract distinguishes historical interval evidence through frontier F from actuation admission at B. It includes seven rows: complete quiet, observed change before F, change after F before B, unregistered writer, sequence gap, epoch change, and irrelevant noise. The fixture encodes writer/epoch/sequence coverage as frozen Boolean fields; it is a method truth-table test, not an event-source or real trace parser.

## Execution and raw results

Construction tests ran once in WSLc: **4/4 PASS** (`construction_raw.txt`, `construction_exit.txt`). The preformal `SOURCE_SHA256SUMS.txt` verified all frozen sources and exact command records before formal execution (`source_integrity_exit.txt` = 0).

The exact one-shot runner is `run_formal.sh`; its launcher is retained in `FORMAL_COMMAND.txt`. It mounted source read-only at `/src`, outputs separately at `/out`, disabled network and image pulls, requested 1 CPU/512 MiB, and used `--rm` with unique names.

| Stage | Invocations | Exit | Retained evidence |
|---|---:|---:|---|
| Candidate | 1 | 0 | `formal_output/candidate_raw.json`, stderr and exit sidecar |
| Independent raw-fixture auditor | 1 | 0 | `formal_output/audit_raw.json`, stderr and exit sidecar |
| Post-run container inventory | 1 | 0 | `formal_output/container_list_after.txt` (header only; no containers remained) |

Auditor stdout: `{"cases":7,"errors":0,"mutations_rejected":4,"schema":"6310-audit-v1"}`. The post-frontier counterexample returns `QUIET_AS_OF_FRONTIER` but `BLOCK` at B because the version changes from 7 to 8 and the atomic compare is false. A pre-F change is `CHANGE_OBSERVED`. Unregistered writer, sequence gap, and epoch change return `UNKNOWN`. Complete quiet and irrelevant noise retain `QUIET_AS_OF_FRONTIER`; actuation is admitted only when the independent compare at B matches.

No candidate/auditor retry, threshold tuning, code change after freeze, model, GPU, GUI, provider, user data, or external action was used.

## Environment caveat and limitations

WSLc emitted: “kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” The 512 MiB limit was requested, but swap/cgroup memory isolation and peak-memory enforcement are unverified.

This result shows only that the frozen implementation and independent oracle agree on these seven Boolean-coverage fixtures and reject four output corruptions. It does not demonstrate that a real GUI has a complete writer set, contiguous event stream, trustworthy epochs, a correct frontier barrier, or an atomic compare-and-act operation. It makes no production-safety, latency, human-tempo, or cross-domain claim. For real interfaces, missing coverage remains UNKNOWN; frontier quietness alone is never safe-to-act at B.

All source and raw artifact hashes are in `SHA256SUMS.txt`; preformal source identities are separately frozen in `SOURCE_SHA256SUMS.txt`. Preserve this scoped PASS as-is; a real-source/GUI transfer would require a separately frozen successor allocation.
