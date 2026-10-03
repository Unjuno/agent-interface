# #6067 source-deadline B01 — prospective one-shot diagnostic

H: every >5ms stable-exposure shortfall in this instrumented profile requires
draw-wait return lateness >5ms. A shortfall with wait lateness <=5ms is a
counterexample; all observed shortfalls with >5ms wait -> association only;
none -> HOLD_NOT_REPRODUCED. No outcome establishes the original A02 rootcause.

T: one fresh native private container/Xvfb on research-6183-t0-20261003:
CPU1,512MiB,swap0,PIDs64,uid501:501,read-only source/root,networknone,capdropALL,
no-new-privileges,tmpfs64MiB. Cached image
sha256:c4839671ed0625dd38a53d8ed542bab16407c2b4c88a5ac84431695438c2b816.
Eight 20ms pulses at epoch+(120i+2)ms and eight fixed captures at+(120i+5)ms.
One producer then one saved-only diagnostic auditor after actual native exit0,
retry0. No original A01/A02/T1 allocation or output is reused. No input/model.

D: full source/plan/auditor/image/commands/guestpaths freeze before native launch.
Six complete copied-data controls exercise the same full auditor admission path;
raw byte pins and journal joins are repaired for semantic mutations, retaining
all trial inputs. Failed controls/auditor stop and remain evidence, no rerun.
Profile decision remains finite/unconditional coverage only for this one block.

C: source snapshots now bracket each draw/clear wait and precede XSync paint;
source-wait journal flush follows paint. This additional work changes pacing,
so it is not a replay and cannot backfill A02 source-wait telemetry. Physical
host exclusivity is not claimed. Exact source/raw/image/isolation/terminal
custody is transport evidence, not external actor authentication.

U: original source scheduling cause, host rare tails and phase efficacy remain
unknown. No pacing repair, width extension, CPU raise or safety claim follows.
Optional cpu.stat.local/schedstat/schedstats-enabled fields are retained but
not independently interpreted; unavailable does not mean zero. Required leaf
cpu.stat raw/typed counters, clock brackets and process counters are validated.
Per-wait nr_throttled deltas bracket snapshots, not exact causal throttle events.

## Scientific boundary

reference.py is the byte-identical A01 scientific cell oracle from retained
source at8527cc62dcd96deabeb9524cac62dc8b0c59c4ce; its 10ms lateness,5ms exposure,
190ms gap and960ms window gates are NOT modified. The diagnostic separately
reports its first gate failure or original_single_cell_eligibility. A single
eligible cell is not a complete114-cell experiment or a scientific PASS.

profile_reference.py is a clearly labeled structural derivative: lateness,
exposure and gap/window overruns are measured outcomes, not completeness failures.
Its diagnostic horizon extends to the last actual extraction if needed; do not
interpret its max_gap as a passed original960ms gate. Source/capture chronology,
source identity/colour, recoverable pixels/hash/type, child/PID/window/epoch,
neutrality and complete eight-event/eight-frame denominators remain hard gates.
The auditor never imports probe/runner/fixture/observer/policy/x11/timing.

The exact signed identity is:
shortfall = draw-wait lateness + wait-to-paint + draw XSync - clear lateness.
Only draw wait >5ms is tested as a necessary condition, not as a dominance ratio
or original rootcause. Source and observer CPU counters are process/window
measurements; do not add unrelated maxima into an end-to-end bound.

## Provenance and method checks

common,x11,policy,timing,observer and fixture_baseline copied exactly from
A02 executed-v1 source (public8527cc62...). fixture_trace changes only source
wait instrumentation/journaling, retaining absolute schedule/finalclear.
probe and runner adapt existing D01/A02 orchestration. No hosted Actions change.
Main intake ec89d27268e2315ffc3b5deaa4491685f115d382, canonical docs unchanged;
#7069 is now merged with its original STOP, and peer Linux timerpath untouched.

New decision/clock/custody/collector gates had observed RED (6+7+2 FAIL) then
GREEN. Independent review found four admission gaps before freeze; runtime/spin
mutations produced seven FAIL and transport/continuity mutations twelve FAIL
before correction. Effective runtime, frozen transport commands/host-clock
order, per-process continuity and disjoint shared cgroup reads now are checked.
Host monotonic times are never compared with guest monotonic times.
Pure method suite22tests; native and I/O wrappers are adapted procedural
code, not claimed strict TDD coverage of every I/O path or full-repository tests.
Use python3 -B -m unittest discover -v for scoped method checks.

Native CLI: python3 -B runner.py --guest-source PATH --guest-output PATH --out NEW.
Auditor CLI: python3 -B auditor.py --raw WRAPPER_RAW --out NEW_AUDIT.
No actual result exists before the frozen native command runs.
