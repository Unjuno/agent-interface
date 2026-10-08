# Issue #8668 T0 A03 — operation-bound stale ACKs

**Disposition:** `PASS_METHOD_SCOPED`; A03-specific normalized decision `SUPPORT_FOR_ID_ATTEMPT_BINDING_SCOPED`.

The independent raw-only auditor reconstructed all 317 frozen schedules with no errors and rejected all 9 decision mutations. An identity-blind, phase-aware comparator made 32 false completion claims and admitted 12 unsafe retries. The operation-ID-and-attempt-bound reducer had zero false completions, false cancellations, unsafe retries, neutral-release aborts, or contradictory-ACK gate failures. The two reducers differed in status or retry decision on 88 schedules.

The stale-receipt tests include an older attempt whose operation ID differs from the active attempt, an older attempt reusing the active operation ID with a different attempt number, both arrival orders around a valid current effect ACK, duplicate delivery, stale cancellation with retry requested, and a no-input control. A delayed active-attempt cancellation ACK received after `EMITTED` remains `UNKNOWN` with no retry. Conflicting active-attempt effect/cancel ACKs produce sticky `CONFLICT_UNKNOWN`, with no accepted ACK authority or retry, in either arrival order. A neutral input-release observation never proves semantic cancellation. Valid active effect acknowledgements and confirmed pre-emission cancellation retain their intended decisions.

## Decision-label correction

The first frozen audit is preserved verbatim at `run-01/audit.json`; it reports `PASS_METHOD_SCOPED` and uses the parent Issue taxonomy label `SUPPORT_FOR_PHASE_REFINEMENT_SCOPED`. The A03-specific frozen H/T/D/C/U defines the narrower label `SUPPORT_FOR_ID_ATTEMPT_BINDING_SCOPED`. `DECISION_LABEL_RECLASSIFICATION.json` maps the verified counters to that frozen A03 label. This post-run mapping changed no raw output, freeze, candidate, or original auditor result; neither formal program was rerun.

## Scope

This is host-only finite-model evidence. The OrbStack preflight failed before listing images because a containerd content-blob read returned `operation not supported`; no container was started or repaired. The candidate and auditor each ran once under the macOS network-deny sandbox, exit 0, with retries 0. No OS input, backend, GUI, application, model, latency, task effect, or product behavior was exercised. A01's `FAIL_HARNESS` and A02's original raw/audit remain unchanged. A02's broader stale-ACK transition gap is supplemented by this A03 model result, not rewritten.

See [FREEZE.json](FREEZE.json), [execution record](EXECUTION_RECORD.json), [run log](RUN_LOG.md), [decision-label reclassification](DECISION_LABEL_RECLASSIFICATION.json), and [checksums](SHA256SUMS.txt). The A03 allocation was recorded on [Issue #8668](https://github.com/Unjuno/agent-interface/issues/8668#issuecomment-6069114258); the separate A02 review HOLD is recorded [here](https://github.com/Unjuno/agent-interface/issues/8668#issuecomment-6068996449).
