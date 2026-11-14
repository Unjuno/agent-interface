# Issue #57 current-source composition crosswalk (2026-11-14)

## Decision

The existing three-arm live result remains valid only for its frozen v1
allocation. Do not edit or rerun its runner as a way to retrofit newer runtime
semantics. The current source has a separate v3 composition that carries typed
partial execution, model-attempt usage, images/wait, refreshed target selection,
post-model evidence checks, and an independent effect receipt. However, the
retained `run_integrated_efficiency_live_v1.py` still imports
`adaptive_acquisition_caller_v2`
and the recorded-model runner wrapper records only CLI-visible output. There is
no current end-to-end three-arm result through the v3 composition and current
public caller.

This is an integration/version boundary, not evidence that the earlier live
comparison was incorrect. Finite previous allocations remain separately
classified; no result is promoted to the current integrated milestone.

## Requirement-to-source/test map

| Requirement | Current implementation | Existing focused evidence | Remaining gate |
|---|---|---|---|
| #52 typed stop and no target on refusal | v3 `_decision`, compiled receipt projection | `test_adaptive_acquisition_caller_v3.py`; `test_compiled_native_caller_composition.py` | Run the selected live comparison candidate through the same caller path. |
| #53 every model attempt, failure, usage, visible image and wait | v3 attempt ledger and model-result contract; `v3_persistent_grounding_adapter_v1.py` maps App Server grounding success/failure metadata | `test_grounding_appserver_usage_transport.py`; v3 failed-call/accounting tests | Connect the validated acquisition/preflight path and all arms to one comparison trace; timeout/late usage semantics remain explicit. |
| #54 schema preflight before authority | `schema_preflight_gate_v1.py`; historical three-arm runner preflights each arm | historical protocol/audit | Candidate must account the current preflight and its failures in the same lifecycle totals. |
| #55 fresh identity after model wait | v3 post-model observation/revalidation receipts | v3 changed-source and same-frame refusal cases | Verify current native/public target identity and scorer provenance in selected live domain. |
| Compiled lifecycle result | `integrated_efficiency_compiled_execution_v2.py` joins compiled core receipt to v3 caller | `test_compiled_caller_handoff_v2.py`; native bridge composition suite | Existing live three-arm runner still calls v2 directly and does not emit this public result shape. |
| Release, no replay, typed recovery | core/bridge/InputOwner plus Win32 and X11 public paths | current focused runtime suites; MAP01 R175-R197 records | Keep native input/release/recovery separated from synthetic caller composition; finish the selected live task gate. |
| Independent application effect | v3 `verify_effect` and evidence reference; fixture scorers | local/FakeX composition tests plus selected live packets | Connect the domain's independent durable scorer; successful core execution alone remains insufficient. |
| #12/#46/#56 comparison integrity | frozen #57 protocol/result v1; existing cold/warm/invalidation/repair design | three-arm mechanics/protocol controls; finite historical result | Candidate must freeze same task/model/settings/order/budget and report cold cost, reuse, invalidation, repair and all failures together. |
| v3 result to frozen #57 task row | `issue57_v3_trace_adapter_v1.py` projects only representable complete attempts and calls the unchanged v1 evaluator once all 18 rows and preflights exist; HOLD retains assigned rows and original preflight/discovery inputs, and caller success must agree with the independent exact-submission score | `test_issue57_v3_trace_adapter_v1.py`, including frozen historical trace round-trip, malformed/missing preflight retention and conflicting-score HOLD | Live v3 task adapters, provider preflight accounting and independent scorer are still not connected. |

## Concrete missing composed-path check

The provider seam is now connected: a synthetic App Server JSONL peer feeds the
retained `PersistentGroundingModel`, the new v3 adapter projects its result or
typed failure into `adaptive_acquisition_caller_v3`, and the public caller result
is appended and re-audited by the Issue #57 attempt ledger. This retains call and
thread IDs, usage, image count, wait, missing usage and unattempted task effect.
A separate public v3 compiled-caller/FakeX test joins the returned core receipt,
release records and effect status in one row. The ledger rejects misleading
release/effect receipts, post-write receipt tampering and deleted row fields.

The retained G10-shaped caller/scorer fixture is now also connected to the same
ledger: its public v3 caller result, compiled receipt, terminal release flags,
independent saved-FODS score and raw FODS digest join in one audited row. The
fixture is FakeX and the FODS predates the simulated actions; it proves result
shape and custody only. It cannot provide a fresh task effect, the frozen #57
telemetry fields (for example `durable_calls` and per-input feedback), or a live
Calc comparison row.

The missing composed-path check is now narrower and concrete: no current
comparison runner joins that provider/preflight path to the v3 compiled core,
actual GUI attempt/evidence, durable independent task scorer, and all three
matched arms in one frozen lifecycle record. The historical live runner remains
v2; no claim of a v3 live comparison follows from the synthetic transport and
FakeX cells. The new projection adapter validates old-protocol compatibility
and preserves HOLD evidence, but it consumes v3 results rather than executing
the provider/GUI/scorer path itself. Do not add a new primitive or runtime for
this gap.

## Next finite work

Next, connect the existing independently scored form task adapters to the v3
compiled-caller entry while retaining the actual terminal receipts and task
history. Reuse the existing schema preflight and App Server adapter above; do
not start from another benchmark implementation. A new candidate must cover
one unchanged reuse, one stale-target refusal with zero old-target input, one
bounded repair with post-model revalidation, one release-unknown result and one
effect-unknown result. Its audit must reconcile all assigned attempts, model
usage, caller output, core receipt, release/effect references and raw hashes
without dropping failures. Only after that candidate passes normal and `-O`
checks should a newly frozen live block be considered; do not recycle the old
allocation, conditions, or results.

## Local verification of the mapped seams

On Windows Python 3.11.9, normal and optimized runs passed:

- `test_compiled_caller_handoff_v2.py`: 15/15 each mode;
- `test_compiled_native_caller_composition.py`: 8/8 each mode (the X server,
  transport and input path use `FakeX`; this is not native-desktop evidence);
- `test_adaptive_acquisition_caller_v3.py`: 14/14 each mode.
- `test_issue57_v3_attempt_ledger_v1.py`: 18/18 each mode, including the eight
  imported FakeX composition regressions and ten ledger-specific cases. The
  joined row keeps the caller's independent effect as unavailable even when
  the FakeX terminal release is verified.

`test_v3_persistent_grounding_adapter_v1.py`: 3/3 each mode. These validate
success projection, preservation of provider failure metadata and accounting
retention when output projection fails.

`test_issue57_v3_trace_adapter_v1.py`: 12/12 each mode. It checks exact v3→v1
task projection, failed/unknown-usage HOLD with source retention, assigned-call
count enforcement, accounting and caller/scorer disagreement,
all-18-row preservation,
missing/malformed-preflight HOLD with original input retention, arm-order
rejection and exact round-trip of the saved historical trace through the
unchanged frozen evaluator.

`research.integration.test_issue57_v3_g10_composition_v1`: 3/3 each mode,
including the retained independent-score caller cases and one joined Issue #57
ledger row. The raw saved FODS digest is checked against the independent score
receipt before append; release evidence is derived from each terminal event in
the returned compiled receipt. The application transport/effect is synthetic,
and the historical FODS is not a post-action artifact.

`test_grounding_appserver_usage_transport.py`: Python 3.11.9 skips 1/1 because
the App Server pipe transport needs Python 3.12+. The available Python 3.13.14
then passed 1/1 normally and under `-O`, now including App Server JSONL → v3
adapter → adaptive caller → Issue #57 append-only ledger → re-audit. An initial invocation used an
incomplete import path and failed before tests; it was corrected and is not
counted as test evidence. The full provider-to-scorer three-arm candidate remains
unimplemented and unverified.

The current public Win32 MCP suite was also rerun from this checkout on Python
3.11.9, normal and optimized, for three source-bound cases: exact `call_id`
result query joined to the task oracle (1/1 each), expiry followed by delayed
release recovery and exact-call effect verification (1/1 each), and producer
exception auto-recovery retaining the original action as UNKNOWN/no-replay
(1/1 each). These tests use fake producer/supervisor/target/oracle components;
they verify public result shape and sequencing, not native Win32 delivery or
MAP01. The separate recorded R175-R197 native evidence remains the evidence for
the scoped MAP01 boundary and is not changed by these test reruns.

Four focused public stdio/MCP caller integrations were also rerun on CPython
3.11.9 normally and with `-O`: exact result-query/task-oracle join, expiry
followed by delayed recovery and exact-call effect, public compiled caller
preserving an unknown producer exception, and automatic exception recovery
while retaining the source action as UNKNOWN/no-replay. All 4/4 passed in each
mode. They use synthetic stdio producer/supervisor/oracle fixtures; this checks
the public caller/result shape but does not supply native Win32 delivery, a
fresh MAP01 effect or a matched #57 comparison.

This crosswalk is offline engineering direction. It does not create a live
allocation, claim a new task effect, supersede the historical result or close
Issue #57.
