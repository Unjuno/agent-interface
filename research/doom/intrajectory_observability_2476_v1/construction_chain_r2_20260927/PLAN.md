# Issue #2476 — cumulative track-drift construction successor

Allocation: `issue2476-track-cumulative-drift-construction-r2-20260927`
Parent: [#2476](https://github.com/Unjuno/agent-interface/issues/2476)
Prior construction r1: immutable `STOP_BEFORE_CONTAINER_START`; zero rows ran.

## H / T / D / C / U

### H — hypothesis

A local corridor bound applied independently at each hop can admit cumulative
track drift: a chain of individually in-corridor observations can walk away
from the path predicted by the original accepted anchor. Keeping a separate
global displacement envelope from that anchor should stop the chain at its
first global-bound violation while preserving exact and bounded trajectories.

### T — smallest falsifiable rung

One deterministic synthetic block: ten three-hop candidate trajectories,
evaluated under two fixed policies: (a) per-hop corridor only, and (b) the same
per-hop corridor plus a 12 px cumulative-drift cap from the original accepted
anchor. The 12 px cap reuses #729's frozen center tolerance; local hop radius is
8 px. Score/margin remain 0.80/0.08, geometry 640x480, max hop age 250 ms,
and frame sequence gap at most two. Inputs are fixed in `cases.json` before
execution. Runner and raw-input-only independent auditor use separate local
Docker processes; no retries or tuning.

### D — decision gates

`PASS_CUMULATIVE_TRACK_DRIFT_BOUNDARY_CONSTRUCTION_ONLY` requires exact three-
hop and exactly-12-px cumulative boundary cases to continue all three hops;
the repeated +8 px per-hop residual case to continue all three under the
per-hop-only comparator but stop the bounded policy at hop two (16 px global
drift); the 4+4+5 px case to stop the bounded policy at hop three (13 px); all
missing/ambiguous/stale/geometry/sequence/abrupt-translation controls to stop
before another candidate; independent audit agreement on every raw step; and
zero physical input emissions. Any mismatch is retained as
`FAIL_CUMULATIVE_DRIFT_GATE` without rerun.

### C — controls

No game, image matcher, GUI, X11, OS input, model/provider, external network,
random seed, predecessor frame/session, or prior #729/#2476 output is read.
The per-hop-only policy is a synthetic comparator, not a controller baseline.
All candidate positions, observations, scores, timestamps, and hashes are
authored fixture inputs. No thresholds or fixtures vary after freeze.

### U — limits

This tests only the arithmetic/state boundary of multi-hop tracking. It does
not establish that a real visual matcher follows one target, that 12 px is an
optimal horizon, that a tracker improves completion, or that action authority,
release, target identity, GUI task effects, model utility, or product readiness
is safe or improved. It is not the formal #2476 BASELINE/TRACKED/ABSTAIN study.

