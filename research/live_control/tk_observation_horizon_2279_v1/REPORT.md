# Tk observation-horizon boundary — retained first outcome

**PASS_OBSERVATION_HORIZON_BOUNDARY_SCOPED.** Issue #2279 remains open.
This is one new 24-case validation of an existing preflight's stated contract,
not a production timeout implementation or a model/task improvement.

## Observed result

Each cell below has two fresh worker processes. Effect delay is the requested
Tk timer; it is not asserted to be the actual callback completion time.

| Condition | Requested effect / horizon | Precheck-only | Post-observation |
|---|---|---|---|
| fast | 50 / 200 ms | COMPLETED 2/2 | COMPLETED 2/2 |
| delayed | 350 / 200 ms | UNKNOWN 2/2 | UNKNOWN 2/2 |
| absent | none / 200 ms | UNKNOWN 2/2 | UNKNOWN 2/2 |
| late | 350 / 500 ms | COMPLETED 2/2 | COMPLETED 2/2 |
| blocked_fast | 50 / 200 ms; 300 ms blocking callback | late COMPLETED 2/2 | late evidence retained, UNKNOWN 2/2 |
| blocked_absent | none / 200 ms; 300 ms blocking callback | UNKNOWN 2/2 | UNKNOWN 2/2 |

The blocked-fast original observations were 317.329455 and 301.041972 ms;
the candidate observations were 301.019871 and 301.093671 ms. All exceeded the
200 ms observation horizon. Their descriptive median/range are respectively
309.185714 / [301.041972,317.329455] ms and
301.056771 / [301.019871,301.093671] ms. This is an imposed-delay discriminator,
NOT a comparative latency benchmark. No speedup or natural stall rate follows.

All 24 worker exits, both Xvfb exits and both externally observed batch exits
were zero. Both private sockets disappeared. Both driver stderr files, all
worker stderr strings and both Xvfb stderr files are empty. The tool console
printed a terminal-environment warning outside those retained process streams;
it was not an application error or a reason to repeat any case.

The unchanged raw-only auditor reconstructed all 24 rows, accepted zero late
candidate completions, and rejected all nine preregistered evidence mutations.
Three source/strict-deadline tests pass. Formal retries, replacements, dropped
rows and post-freeze source edits: zero. Construction's 12 cases are excluded.

## Exact delta and meaning

Pinned source: `experiments/x11_dwell_unknown_preflight_2279.py`, Git blob
`f60bd81d37f574337d8aebb9a02fe35b12ab26fd`. The original README defines
completion as observing the fixture effect before the horizon. The loop checks
its clock before `root.update()` but can classify a late observation after that
call returns. The research candidate replaces only these two assignments:

```python
observed_at = time.monotonic() - start
state = "COMPLETED" if observed_at < horizon else "UNKNOWN"
```

The same measured `observed_at` is retained even when late. The selected source
copy additionally receives one CASES entry and passive instrumentation. Both
arms use identical wrappers; blocked cases schedule a real Tk callback that
sleeps 300 ms. Effective AST hashes are frozen per policy/condition.

A postcheck prevents an unsupported within-horizon label; it does not interrupt
Tk processing, guarantee return by the horizon, undo a late effect or authorize
retry. Widget config/cget events are actual toolkit state, not independent
physical screen observations. The original `unsafe_timeout_as_completion`
summary merely counts UNKNOWN and is not treated as an actual safety outcome.
`proceeded` is only a Boolean; no action is dispatched.

## H / T / D / C / U and proof

The complete prospective plan, conditional derivation and SI variable table
are retained unchanged in PLAN.md. H tests observation-time labeling after a
blocking call. T is six conditions, two policies and two fresh repetitions,
in two fixed serial 12-case batches with reversed policy order. D requires
complete raw/source/process accounting, ordinary-condition agreement, two
original late-completion witnesses, zero candidate late completions and all
controls. C includes the explicit delay and the non-preemptive update call.
U excludes real task effects, calibrated dwell distributions, model uncertainty
use, timing benefits, arbitrary applications and production adoption.

The inequality argument is a code invariant, not an experimental discovery:
a pre-call clock check says nothing about an unbounded later return. The live
experiment tests its manifestation in this exact Tk fixture. No historical
preflight or its earlier scoped result is rerun or erased.

## Environment and chronology

Provided Linux x86_64 execution container, kernel6.18.44/glibc2.41,
CPython3.13.5, Tcl/Tk8.6.16; fresh authenticated Xvfb640x480x24, TCPdisabled.
CLOCK_MONOTONIC; allowed guest CPUs0..4, no affinity/frequency pinning. No
Docker/OrbStack engine/image attestation, model/provider, input, user documents,
installation or experiment network. Source/binary identities in ENVIRONMENT.
One case per fresh worker, 4 s worker timeout; each batch supervised at30 s.
Recorded worker-span diagnostics were11.374 and11.356 s. These exclude server
setup/teardown and are not end-to-end task metrics or timeout proofs.

Intake main e4c2e58122aa138e421048d8e86ec18259143b9e. Public hash-freeze commit
34320fbd36624f7b83ca6b1d1a2555b60b4e653d, Issue comment5768314792 preceded both
formal batches. Full source bytes are published afterward; the earlier commit
is explicitly a hash commitment, not earlier public source availability.
FREEZE.json SHA256 e825fb5d3837c3c1a95133e46d883093975b79ed68a921a87fe58740ce45b5b2.
First result comment5768330469. All seven source/plan/environment hashes remain
unchanged. Same-author independent implementation/process is not external
human review. Repository CI/review and merge are separate delivery gates.

Raw batch0 SHA256 a0dae73e773e52623b4182c89cea0038ae35e766ea64a998d23eedab190fe95a.
Raw batch1 SHA256 e5b48076f76ec2569b6105f4d9e0c28b72babc8933f790b7724d5c20353a406b.
Audit SHA256 75cee4ada8099f0ca9a988cb6afa416e1b6e0f8c7c341b4937d1ef6c327404ba.

## Preservation and integration decision

Only the new study path is added. Shared runtime, the original preflight,
root direction and previous evidence remain unchanged. Earlier pause evidence
is already handled by #4000; no duplicate publication. Earlier chat-local X11
coalescing remains HOLD_EXTERNAL_EXIT_UNOBSERVED, not recovered by this result.
Its archive reference stays in PLAN.md; that large old ZIP is not claimed to
be included here. Local setup/publication incidents remain under #2279.

Concrete integration constraint: keep observation acceptance deadlines distinct
from event-loop entry checks and from hard execution deadlines. This result
supports the small post-observation classification change for this fixture,
not automatic runtime promotion. The broader #2279 two-family calibration,
model-facing uncertainty and task-benefit requirements remain unresolved.
Global ROADMAP is not completed by a component result.
