# #1964 — censored useful-effect membership

Successor to closed #1838, whose formal.py blob is
`0cd5eb1da1d763671b79482582685e83275ab451`. Parent source and result stay intact.
Base: `5432f3aa2374753e7ab206ad5e1f3f093ac0a641`.

## H
Given D in [dl,dh], R in [rl,rh], D<=R, and exact same-clock useful-effect E
with independently established ACTION causality, membership in half-open [D,R)
can remain UNKNOWN. Define T as true in all feasible worlds, F as true in none,
and U otherwise. No-effect or ENVIRONMENT is F. The closed integer edge intervals
describe uncertainty, not exact physical occupancy.

Candidate: T iff dh<=E<rl; otherwise U iff dl<=E<rh; otherwise F.
Reject non-integer/malformed/infeasible bounds, unknown cause and noninteger E.

Proof sketch: existence needs a feasible down<=E and up>E; choosing dl and rh
witnesses it exactly when dl<=E<rh. Universal membership requires every down<=E
and every up>E. When the down/up domains overlap, a zero-duration feasible world
already falsifies universality. When disjoint, dh<rl and the extrema dh,rl give
the exact universal condition. This argument is conditional on all D<=R pairs
being feasible; correlation or stricter positive-duration assumptions are new models.

## T
Construction: 8 directed toy cases, grid 0..2 only. Formal: every integer edge
domain within 0..6, dl<=dh, rl<=rh, dl<=rh; effects None,-1..7; two causes.
One formal invocation only; exclusive INVOCATION marker before evaluation.
RAW.json stores one row per edge domain and a 20-character verdict vector ordered
by cause ACTION,ENVIRONMENT, then effects None,-1..7. No samples are discarded.
Auditor independently enumerates every feasible D,R world without importing
candidate.py, reconstructs the complete corpus, checks exact edges, all single-step
inward refinements, and a shared-observation true/false witness. It rejects six
corrupted copies even after their raw digest is recomputed where applicable.

## D
PASS_CENSORED_USEFUL_EFFECT_MEMBERSHIP_SCOPED requires candidate/reference equality,
some U, no exact-edge U, no known-verdict reversal after refinement, a valid
opposite-label witness, invalid-input rejection, 6/6 tamper rejections, verified
frozen source, one formal run, no rerun/replacement/tuning. Otherwise retain FAIL
or infrastructure STOP; no same-identity correction after formal begins.

## C / U
Parent #1838 remains valid for its known-interval predicate. This successor changes
the evidence model and declares half-open rather than parent's inclusive membership.
Integer time, one key, same clock and established causal usefulness are assumptions.
No physical truth, live clock, causal-discovery, occupancy-duration, performance,
model, gameplay or human-tempo result follows. A point effect does not identify
the duration of useful control. No shared runtime or old evidence is modified.

## Execution and retention
Use run_container.sh SOURCE OUTPUT construction.py|formal.py|audit.py in WSL Linux.
Bubblewrap uses new network/PID/IPC/UTS/user namespaces, read-only /usr and source,
private proc/dev/tmp and only a dedicated output directory writable. No host home,
desktop socket, credential, provider or external network is mounted. Host kernel
is shared; this is process isolation, not a timing-comparable VM.
Freeze source and SHA-256 manifest in GitHub, read back exact content, then execute.
Retain RAW, RESULT, AUDIT, invocation, environment and first-outcome logs.

Next only on PASS: check whether real receipt schemas preserve these endpoint
constraints before interpreting useful-effect membership. #1928 remains separately
owned and no live/model allocation is consumed here.
