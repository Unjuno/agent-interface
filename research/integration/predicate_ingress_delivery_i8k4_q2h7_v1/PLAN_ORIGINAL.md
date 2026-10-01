# Typed predicate ingress — engineering verification i8k4

## Origin, goal and additive ownership

Repository: Unjuno/agent-interface. Intake main: 4a1f3957e91b412a64769199f78f2c4b0102d28b.
Source: research/analysis/predicate_cache_persist_4217_v1/experiment.py,
Git blob 51373e57f9966c7ca8d8518a218d02363867fb81.

Closed #4236 / merged PR #4244 retained HOLD_AUDIT_GATE_SPEC_ERROR. This work neither
reruns those consumed allocations nor changes their source, records or decision.
Its changed engineering boundary is **current-state and JSON ingress validation**,
not persistence, dependency completeness, cached value correctness or a repaired
historical auditor. It is an opt-in adapter around the exact predecessor, not a
claim that deployed Agent Interface uses this research predicate.

Proposed additive path: research/integration/predicate_ingress_i8k4_v1/.
Proposed branch: engineering/predicate-ingress-4236-20260925-i8k4.
Neither is claimed created remotely. No existing repository file is changed.

## H — falsifiable engineering requirement

Valid UTF-8 requests, typed current states and well-formed cache artifacts retain
the predecessor's complete result, including its diagnostic fields. Invalid
current states return INVALID_CURRENT_STATE before any predecessor prepare,
consume or truth call. Invalid request/wire returns its typed rejection before
those calls. An invalid/absent cache under a valid current state becomes a cache
miss and recomputes; it does not throw due to unhashable JSON array/object fields.
All adapter replies deny action authority and leave task_success null.

This makes explicit a stronger supported input envelope. It does not retrospectively
assert that #4236 promised malformed current-state support.

## T — frozen local check, not public preregistration

Provided Linux/CPython standard-library execution container; see ENVIRONMENT.json.
No Docker/OrbStack image attestation, installs, model/provider, GUI/native input,
user records, shared runtime or experimental network traffic. A failed raw-GitHub
DNS materialization attempt is recorded separately. Exact source was then copied
from the successful GitHub MCP read and its Git blob ID recomputed byte-exactly.

110 exact input byte strings are frozen in CORPUS.json:
12 VALID; 61 CURRENT_INVALID; 17 ARTIFACT_INVALID; 11 WIRE_INVALID;
9 REQUEST_INVALID. Both BASELINE and ADAPTER receive each exact input in a fresh
worker: 220 workers total. Arms alternate order by case index. There are no random
samples, model labels or measured throughput/latency benefits.

The additional bool_alias_one case uses a valid artifact whose intent_version is
integer 1 and a current state whose corresponding value is true. Integer-valued
floats for each generation are separate cases. Currentness string "false", null,
missing fields, arrays/objects, duplicate JSON keys, nonfinite constants, float
overflow, length/depth bounds and malformed artifact fields are retained explicitly.

Eight unit methods plus a separate 6-input/12-worker construction sample and 14
copied-evidence controls precede freeze and are excluded. The full 110-input matrix
has not been run before freeze. A local Git commit and FREEZE.json bind source,
corpus, environment and this plan before exactly one engineering invocation.
This is a LOCAL engineering check, not a GitHub-preregistered scientific allocation.

Each worker has a 3 s supervisor limit; its real exit/stdout/stderr/PID/argv and
monotonic brackets are retained. The outer process limit is 24 s within a 30 s
tool invocation. Records are flushed after each worker. A failed/incomplete worker
stops the allocation, with no retries, replacements or changed thresholds.

A worker's expected exception from BASELINE is captured as an observation. Its
process exit0 is not misreported as a successful predicate operation. Function
entry counts use sys.setprofile with exact filename/code-name selection; these
are declared instrumentation, not timing measurements. The adapter does not
receive case IDs, group labels or the independent oracle.

## D — decision gates

PASS_LOCAL_TYPED_INGRESS_ENGINEERING requires all 110 exact cases / 220 worker
receipts, the true outer exit0, complete source/corpus hashes, exact independent
response reconstruction for both implementations, valid-input parity, zero
predecessor calls for invalid current/request/wire, invalid-cache misses, neutral
adapter flags, no unexpected ADAPTER exception, and all 14 effective copied-evidence
mutations rejected with a passing positive baseline. No-op controls and auditor
crashes do not count as rejection. Complete semantic disagreement is FAIL;
source/process/coverage/audit ambiguity is HOLD/STOP. There is no performance gate.

Group counts come from the frozen corpus; totals are checked before execution.
No per-policy denominator is equated to a two-policy denominator. The old #4236
HOLD remains unchanged regardless of this result.

## C — competing explanations and deliberately excluded claims

Python's bool/int relationship, truth-value testing, JSON duplicate handling and
nonfinite-number defaults are known language/library semantics. This is source-
bound engineering validation, not discovery of a new Python issue or a security
exploitation study. BASELINE returns from malformed states are violations of this
new ingress envelope, not measured real-world unsafe actions.

The adapter performs no generation coercion and supports arbitrary nonnegative
Python integers subject to the interpreter's JSON integer-string limit. The wire
budget is 65,536 bytes and maximum nested container depth is 32. UTF-16/UTF-32,
nonfinite numbers even in irrelevant fields, repeated object names and deeper or
larger requests are intentionally unsupported. Extra current-state fields are
ignored only inside this supported bounded JSON domain, as in the predecessor.

A valid artifact digest is not authenticity or semantic truth. The declared
predicate dependencies must still be complete; caller state must come from a
trusted/current source. Malformed cache recovery does not authenticate current
state. No blanket exception catching around predecessor execution hides a new
internal error. Memory exhaustion, interpreter faults and hostile filesystem
mutation are outside this finite support claim.

The unchanged predecessor eagerly evaluates truth even on cache hits because it
returns oracle/correct diagnostics. This adapter preserves that behavior; reused
is NOT evidence that predicate evaluation or a model call was avoided.

## U — uncertainty and limits

One exact research predicate and one Python environment, deterministic directed
inputs and same-author separately implemented auditing. This is not external
human review, natural fault frequency, formal universal proof of all JSON input,
model accuracy, public CLI/MCP adoption, cross-platform support, crash durability,
input authorization, task completion, latency/token benefit or whole-roadmap completion.
Counts/byte identities are exact discrete observations. Timing is diagnostic only;
no combined physical standard uncertainty or coverage factor is estimated.

## Input/measurement variable table

| Name | Japanese meaning | SI unit / convention | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| raw | 受信要求の原byte列 | SI dimension 1; byte information unit | handle_wire input | immutable bytes; supported length 1..65536 | byte vector |
| request | 復号後の要求 | 1 | strict UTF-8/JSON decode | exact prepare/consume envelope | mapping |
| state | 現在状態 | 1 | request.state | five nonnegative integer generations, bool currentness, allowed intent; extras ignored | mapping |
| artifact | 以前の述語結果 | 1 | request.artifact | validated cache or explicit miss | mapping or JSON value |
| generations | 世代識別値 | 1 | form/required/intent/producer/source counters | exact int, not bool/float, nonnegative | integer scalars |
| status | 検証結果の分類 | 1 | typed adapter reply | OK/PREPARED/INVALID_WIRE/INVALID_REQUEST/INVALID_CURRENT_STATE | categorical |
| calls | 既存関数への呼出回数 | 1 | profile entry counts | one isolated worker invocation | integer vector |
| times_ns | プロセス・関数時刻 | s, encoded as ns | monotonic_ns receipts | same host clock; ordering diagnostic only | integer scalars |

Unit check: request length and its threshold both count bytes; depth and function
counts are dimensionless. Monotonic brackets are compared in the same nanosecond
unit and are not equated to application/input effect times.

## Conditional correctness argument

1. handle_wire checks immutable raw type/length and strictly decodes it. Duplicate
   keys, nonfinite values and unsupported depth fail before request dispatch.
2. Exact request keys and supported operation/policy are checked before state use.
3. Every required state field is present and has its exact required type/domain
   before any predecessor function is called. Therefore Python numeric equality
   cannot equate a supplied bool/float with an integer generation on accepted input.
4. On prepare, validated state is passed unchanged to the exact predecessor.
5. On consume, safe artifact shape/type checks precede predecessor validation.
   A valid artifact and state are passed unchanged, so the complete result is
   identical to the predecessor. When validation fails, None is substituted;
   the predecessor treats this as a cache miss and evaluates the valid current state.
6. Every adapter return is created by one response constructor whose authority,
   input_dispatched and task_success values are constant. No OS execution occurs.
7. These source implications do not prove that an accepted current observation
   is authentic/current or that the predicate captures all task dependencies.
   They prove only the conditional typed ingress/legacy delegation contract.

ERROR CHECK: valid/invalid wire, invalid current state and malformed cache are
separate dispositions; cache misses are not current-evidence refusal; diagnostic
executable does not grant OS authority; source identity is not source authenticity.
The finite matrix and independent audit test this argument's implementation.

## Roadmap / publication boundary

Intake and bounded collision search -> exact source -> excluded construction ->
local freeze -> one bounded engineering matrix -> raw-only audit/14 controls ->
complete additive source/raw/report patch -> permitted GitHub Issue/PR publication ->
exact-head CI/review -> qualified main readback -> dependency-safe owned-ref cleanup.

The current session exposes read-only GitHub MCP actions. The enabled GitHub plugin
search did not expose a separate writer; gh/docker and named GitHub token variables
are absent in this container. This is a local capability limit, not a fleet outage.
No bypass, alternative account or changes to permissions are attempted. Publication
and main integration remain pending, not silently satisfied by local artifacts.

## Primary references

- GitHub exact source at the pinned main/path above; prior #4236 and #4244.
- Python 3.13 JSON documentation: https://docs.python.org/3.13/library/json.html
- Python bool documentation: https://docs.python.org/3.13/library/stdtypes.html#boolean-type-bool

Documentation was checked on 2026-09-25 and currently renders 3.13.15; the measured
interpreter identity is recorded separately and is 3.13.5, not relabelled 3.13.15.
