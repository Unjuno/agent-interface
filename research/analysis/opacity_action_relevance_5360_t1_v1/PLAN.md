# Issue #5360 T1 — action-relevant opacity successor

Predecessor #5360 T0 remains immutable. T0 reported two histories in which a
final-state serializability predicate accepted an action after a read whose
producer later aborted or completed only after the read. T1 changes the
scientific discriminator by explicitly separating action-relevant reads from
presentation-only reads and crossing them with transaction status and
generation coherence.

## H / T / D / C / U

**H.** An action-relevance- and generation-aware opacity audit rejects
action-authorizing reads from aborted, rolled-back, uncommitted, or superseded
evidence while preserving harmless presentation-only reads; a final-state-only
predicate accepts at least one of these unsafe histories.

**T.** Deterministically exhaust 8 declared lifecycle patterns × 2 read-use
roles × 2 policies = 32 rows. Patterns: clean commit, read-then-abort,
delayed completion, mixed generation, supersession, rollback-after-read,
duplicate completion, and tentative presentation. Roles: read explicitly
consumed by action vs display-only and not consumed by action. Policies:
`FINAL_STATE_ONLY` and `ACTION_RELEVANT_OPACITY`. Each row retains the full
strictly monotonic event history, read provenance, consumer dependency, final generation,
decision, first invalid read, and oracle result. This is a deterministic
finite host experiment; a container run is separately gated by #5085.

**D.** The auditor reconstructs status, action use, and generation at the exact
consume event exclusively from the ordered raw event list; scenario labels and
cached provenance are not oracle inputs. Sequences must be unique and strictly
increasing. `PASS_T1_SCOPED` iff (1) the final-state-only comparator accepts at
least one action whose consumed read is invalid; (2) the opacity checker
rejects every action depending on a read that was not committed and valid at
consume time, was later aborted/rolled back, or has a generation different
from the action epoch; (3) all valid committed same-generation action reads
remain admissible; (4) display-only reads never cause an action and do not
cause opacity rejection solely for being tentative; (5) first invalid-read
provenance is retained; (6) an independent history oracle agrees on all 32
rows and rejects three in-memory corruption controls. Any invalid action
admission is FAIL; any absence of a comparator witness is HOLD_NO_DISCRIMINATOR.

**C.** Hand-authored deterministic histories; no real transaction manager,
irreversible side effect, network fault, probabilistic observation, or
malicious component. Final-state-only is an explicit weak comparator, not a
claim that a production serializability implementation behaves this way.

**U.** Real action relevance, irreversible effects, distributed commit,
retries, probabilistic observations, concurrent read/write-set semantics, and
whether generation numbers capture all semantic dependencies.

## Frozen controls and execution boundary

Two policies, fixed scenario matrix, no post-hoc tuning. `action_consumed_read`
is explicit and distinct from `presentation_only`. The opacity decision must
record the earliest invalid consumed read even when a later rejection also
exists. Raw output is append-only and overwrite-protected; independent auditor
does not import the simulator.

One runner invocation; one separate audit. Docker/OrbStack formal execution
requires an exact named exclusive CPU-only allocation and current-main/source
readback in #5085. Latest #5085 checkpoint expressly prohibits Docker CLI
inventory/inspect until a coordinator assignment names this task/allocation,
base SHA, and bounded exclusive window. No container invocation is authorized
or claimed by this plan. Host construction checks are separate evidence and
cannot be promoted to container/formal execution.
