# Saved-effect checkpoints in the current phased caller

An interrupted input program can already have saved the requested values. The
previous Calc diagnostic proved this before a later model decision proposed
another Save. Expanded typed phase feedback did not consistently remove that
proposal in the fixed-context experiment. This candidate instead connects the
existing non-final artifact sampler to the current cause-servo / Executor9 stack
and uses an explicit, caller-declared completion policy.

The actual Calc episode completes with two screenshot-based model decisions and
one submitted Save chord. The first checkpoint is UNKNOWN with empty saved cells;
the model then clicks the visible Excel format confirmation. The next checkpoint
is VERIFIED for A1=480 and A2=192. The caller requests independent final scoring
immediately, with no further input, passive sampling or model call. The final
workbook and independent score agree.

## Integration and evidence scope

`checkpoint_cause_interactive_v1.py` reuses `effect_checkpoint_v2.Checkpoints`,
including its bounded immutable byte archive. It samples the real private
fixture output while the application is open. The exported teardown copy is
not the source of the intermediate evidence. Executor9, cause-servo input
admission, release checks and `phased_submit_v1.py` are unchanged.

`checkpoint_cause_socket_v1.py` adds request-scoped checkpoint boundaries to the
stopped socket path, using existing request correlation and CommandOnce3.
`durable_submit_v5.py` commits a pending query before transport, assigns its
request ID, and resolves only an echoed query with a matching scoped reply or
correlated rejection. It validates declared contracts and VERIFIED values/digest
shape. UNKNOWN and busy replies resolve the query, without proving completion.
Lost or conflicting replies retain pending state and block new commands; an
explicit command-free read carries the original query ID. No command is resent.

The journal format is **durable-submit-v5**. Existing v4 journals and
format-specific recovery/outcome presentation helpers are not migrated by this
experiment. The unchanged phased helper works because it consumes the shared
result fields. The reusable worker supports saved cells and a local form value;
this current-stack live measurement covers Calc only. Unsupported application
contracts are rejected.

The model prompt and `completion-policy.json` disclose file evidence and the
finish-on-VERIFIED policy before the first decision. This is an artifact-enabled
profile, not a pixel-only GUI baseline. The model receives the first UNKNOWN
reply along with the original interrupted-program evidence and a new screenshot.
The positive reply is consumed by the declared caller policy, not concealed in
model input or presented as a model judgment.

VERIFIED means the archived sample matches the declared cells on the first
worksheet. It does not establish input-to-effect causation, whole-workbook
equivalence, atomic sampling, persistence after power loss, or whole-task success.
The query does not close the observation window, renew a lease or grant input
authority. The final independent evaluator remains required for this task.

## Measurements

All values below come from `results/checkpoint-decision-calc-01/audit.json`.
There is one fresh private Linux/X11 Calc episode, seed238, with the existing
numeric pointer-first proposal schema. The runner requests gpt-5.6-luna / low;
the actual served model identity and monetary cost are not independently known.

| Measurement | Observed value |
| --- | ---: |
| Actual model decisions | 2 |
| First capture to independent evaluation | 22.155 s |
| Model runner durations | 10.274 / 7.720 s |
| Model input / output tokens | 20,085 / 406 |
| Reported cached input tokens | 13,824 |
| Durable exchanges, excluding initial and finish | 17 |
| Runtime events / exact transported frames | 95 / 16 |
| UNKNOWN query caller round trip | 86.874 ms |
| VERIFIED query caller round trip | 117.662 ms |
| Query runtime receive to evidence emission | 54.585 / 71.047 ms |
| Activation-to-tail handoff | 217.747 ms |
| Additional passive decision samples | 1, taking 327.057 ms |
| Submitted Save chords / input after VERIFIED | 1 / 0 |

Query round trips use the Linux caller clock and include journal and transport
work. Runtime receive-to-emission uses the runtime clock. Model runner durations
use the Windows runner clock; no Windows/Linux clock subtraction is used. These
are observed samples, not latency guarantees or percentiles.

Both the Save tail and confirmation click terminate with `needs_decision` after
focus changes. Their release checks pass. The checkpoint does not relabel those
programs as completed: successful saved effects and interrupted execution coexist.

The earlier sampled-effect Calc episode needed four decisions and 45.181 s.
The new capability, completion policy, prompt and separate model samples change
the conditions, so this is not a paired speedup or token-compression result.
The supported conclusion is narrower: explicit saved evidence can end this
episode after confirmation, avoiding another decision and Save.

## Validation and retained artifacts

`probe_durable_checkpoint_v1.py` records ten reconciliation controls: matching
VERIFIED/UNKNOWN, unrelated ID, wrong contract, wrong typed value, improper task
success, missing digest, conflicting command, busy reply and correlated rejection.
A stateful transport control times out after the echo, refuses a new command
before transport, then resolves with one explicit read and one query write total.
A simulated lost response retains the pre-transport pending state. Thirty-one
archived submit/clock replies reconcile identically under v4 and v5. These are
protocol controls, not a live socket-loss experiment.

`audit_checkpoint_decision_calc_v1.py` passes on the live archive. It verifies
source hashes, exact event slices/cursors, all durable resolutions and receipts,
35 journal records, model image/prompt/raw-response provenance, target checks,
shared phase replay, passive sample replay, all pre-deadline admissions and empty
verified input releases. It decodes all 16 transport frames exactly. It reparses
both archived workbook samples and independently reads their cell values and
hashes after the private source file has been removed. Only `finish` follows the
VERIFIED reply; the final saved workbook is independently checked again.

Artifacts:

- `results/durable-checkpoint-controls-01/`: controls, recovery trace, source hashes.
- `results/checkpoint-decision-calc-01/`: policy, prompts, model outputs, journal,
  requests/replies, images, raw transport frames, both checkpoint byte archives,
  final workbook and audit.

The opt-in candidate does not change the default client or older frozen runs.
The worker's existing CPU/GIL and blocked-output limitations are not re-tested
here. Next test actual query response loss with command-free recovery, then a
different saved-effect task through the same caller. Issues #34 and #39 motivate
this work, but their broader effect attribution and outcome requirements remain
open. Human-like live tempo and the Domain Coverage Matrix remain the goal.
