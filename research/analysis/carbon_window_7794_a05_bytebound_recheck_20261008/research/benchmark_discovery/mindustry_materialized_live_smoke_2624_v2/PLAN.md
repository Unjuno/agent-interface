# Issue #2624 live-smoke scorer-correction plan

Allocation: `mindustry-materialized-live-smoke-2624-20260926-02`.

This is a new allocation under the **same scientific question** as consumed v1.
V1 remains `FAIL_ORACLE_MISMATCH`; no row is reused or relabelled. The sole
scientific-gate correction is the orientation/reference interpretation proven
from retained raw bytes after v1: the v1 formal `oracle.json` Git blob is exactly
`fb7cd0e88e730401b32c2954b58c8c02ec83fcc6`, which is also the historical
create/reload-1/reload-2 oracle blob already retained on main.

## H
The exact pinned fixture can satisfy the intended historical canonical-projection
gate when the scorer binds the actual retained oracle identity rather than the
v1 transposed width/height interpretation. All launch, readiness, zero-input,
window, timeout, and cleanup gates remain unchanged.

## T
One fresh session only; no retry/replacement/tuning. Exact same fixture members,
60 s timeout, fresh HOME/XDG/data, private Xvfb/Openbox, Java21, no controller,
task input, model, or provider calls. The runner/auditor additionally require
historical oracle Git blob `fb7cd0e...fcc6`. Its decoded shape is
width=250,height=300 with 300 tile rows of 250 columns. No v1 formal files are
input to the runner.

## D
`PASS_MINDUSTRY_MATERIALIZED_LIVE_SMOKE_SCOPED` iff exact fixture identities
pass; Xvfb/Openbox start; Mindustry remains alive through readiness; `ready.txt`
and `oracle.json` arrive <=60 s; oracle Git blob exactly equals the historical
retained blob; decoded fields are width=250,height=300, paused=true,
core_present=true,copper=200 with 300x250 tile matrix; a Mindustry top-level
window exists; all task/controller/model/provider counters remain zero; all
owned processes terminate without SIGKILL and are reaped; independent audit and
corruption controls pass.

Exact assets but no readiness/window -> `FAIL_LIVE_FIXTURE_STARTUP`.
Ready oracle differing from historical blob/shape/scalars -> `FAIL_ORACLE_MISMATCH`.
Missing source/process/evidence -> `STOP_OR_HOLD_EVIDENCE`.

## C
This corrects a preregistered scorer interpretation, not the application or
fixture. The historical oracle reference existed before v1 and is not chosen
from v2 outcomes. V1's failure remains immutable.

## U
One setup-only live session. No reset reliability, task correctness, controller
behavior, model economics, token/latency benefit, human tempo, or production
claim. A PASS only removes #1679/#57's live-start gate.
