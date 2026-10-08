# Issue #6604 T0 — disturbance-timescale route-profile method test

Allocation: `DISTURBANCE-TIMESCALE-6604-T0-ORBSTACK-20261002-01`  
Scientific base: `2c92d3979d5cdbeadef1fb1225ac9f60a206035c`  
Runtime: OrbStack, CPU-only, pinned cached Python image, `--network none`.

## H / T / D / C / U

**H.** In a finite discrete plant with identical exposure and action vocabulary, direct and fixed-period local feedback can reverse route ranking between slow drift and rapid reversal; pooling the two strata can choose the wrong route. A no-crossover control must not produce a spurious reversal. A semantic target-swap with no observable cue must be UNKNOWN/ineligible, never scored as a tracking success.

**T.** Enumerate deterministic trajectories for slow drift, near-cadence reversal, abrupt step, no-motion, and an unobservable semantic swap. Compare two fixed laws over the same 12-tick horizon, one command opportunity per tick, and one action vocabulary/cap: the direct route samples target observations every three ticks and applies immediately; the local-periodic route samples every tick and applies each command after one tick. The plant is one-dimensional with bounded action, explicit observation age, action lag and terminal release receipt. Include a planted slow-versus-fast crossover and a no-crossover slow/medium pair. Candidate sees only controller-visible numeric target observations and its own state/action receipts; a separate oracle file holds semantic validity. The independent auditor recomputes every state/action/effect row from the frozen schedule and plant definition.

The two route laws are method fixtures only; they are not claims about or implementations of #6061/#6089. No learned or adaptive controller, model, GUI, user data, or external actuation is involved. This fixed-law pair intentionally tests the T0 analysis contract only.

**D.** `PASS_METHOD_SCOPED` iff the candidate and independent replay agree exactly; the planted slow-vs-fast ordering reversal is recovered; the no-crossover arm has no reversal; all schedules have identical horizon/opportunity accounting and satisfy the frozen hard safety/release gate; target-swap is UNKNOWN; and timestamp, omitted reversal, unsafe-input, pooled-only, and fabricated-effect corruptions are rejected. Any mismatch is FAIL_INTEGRITY; any unsafe or false effect is FAIL_SAFETY; missing receipt/oracle is HOLD.

**C.** A universal simple route could dominate every eligible stratum. Any planted interaction can be a defect of the synthetic parameterization, unequal opportunity, latency, or scorer rather than real route behavior.

**U.** This no-model finite discrete plant cannot establish a GUI/DOOM effect, feedback advantage, real timing profile, safety or release behavior, model/tool cost, human tempo, general frequency law, or product benefit. No transfer to a runtime or claim about #59/#57 is made.

## Freeze and one-shot policy

The case matrix, plant equations, controller laws, scorer, mutations, commands, image digest, source hashes and raw/audit paths are frozen before formal candidate launch. Candidate once; only on exit 0, independent raw-only auditor once; retries zero. Raw output and all failure/stop evidence remain immutable. Resource requests/configuration are not claimed as effective enforcement unless measured.
