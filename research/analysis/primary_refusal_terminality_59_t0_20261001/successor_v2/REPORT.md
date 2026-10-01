# Issue #59 successor T1 — fail-closed response parsing

## Disposition

`PASS_PARSE_FAILURE_TERMINALITY_CONSTRUCTION`. The separately frozen v2 caller
candidate moves envelope parsing into the same failure boundary as the host
presentation/send call. In the frozen deterministic cases, explicit refusal,
malformed returned envelope and thrown transport/presentation error all latch
STOP before a second effectful call reaches the host. The public close call
remains available. Valid completed input remains usable only with a verified
neutral release.

This is a host-local construction result, not a live integration or production
runtime PASS. Parent T0's `FAIL_UNCERTAIN_DELIVERY_REPLAY` remains unchanged.

## Frozen experiment

- Issue #59; allocation `59-primary-refusal-terminality-host-t1-20261001-02`.
- Main base `975aed8ad7923a109cfb445b4028d18a10088f63`.
- Current PR #5639 head at freeze: `5fc859f40dcd1bf39aaa9a2f5a78425c47a717cb`.
- Parent source blob from `9c7735a8c890e77fb9c51c6c4e93addeeba3158b` was
  re-read at the current PR head and remained byte-identical.
- Host: Node `v26.7.0`, deterministic mock only. No network, model, GUI/X11,
  OS input, container, or external effect. No exclusive container lease for
  this allocation was recorded in #5085.
- Construction tests: PASS for explicit refusal/image, malformed envelope,
  transport throw, and valid input/release.
- Candidate invocation 1, exit 0; raw SHA-256
  `534f954c09cf9680971a60ad3d3f4e5bb4d5c65001856187b85d628414335b50`.
- Independent raw-only audit invocation 1, exit 0; 4 rows, zero errors; audit
  SHA-256 `5c3bf76c9b98d0a7bb924c1d43ce1ec979db3a3cf326dd63060ded0fb46a6f54`.
- No retry, post-result tuning, or candidate replacement.

| Case | STOP latched | Post-fault effectful calls | Close | Outcome |
|---|---:|---:|---:|---|
| Explicit refusal with text+image | yes | 0 | allowed | pass |
| Malformed envelope | yes | 0 | allowed | pass |
| Valid completed input + verified neutral release | no | 1 valid continuation | allowed | pass |
| Transport/presentation throw | yes | 0 | allowed | pass |

## Interpretation and boundary

This successor addresses the exact failure observed in T0: the former caller
let `read(reply)` throw outside its catch/latch boundary. It shows the local
candidate's error-containment contract on stipulated mock responses. It does
not establish that the actual relay always returns these shapes, that a live
primary stops after its tool-call exception, or that any real input was
released, delivered once, or produced a task effect. The v2 candidate is a
reviewable construction artifact only; it has not been integrated into PR
#5639's frozen caller or exercised against MCP/X11.

Next, promote only the smallest parse-boundary change into a newly frozen live
allocation after source review, current-main compatibility, shared-resource
lease, and all requirement-to-test gates close. Do not rerun or alter either
retained allocation.
