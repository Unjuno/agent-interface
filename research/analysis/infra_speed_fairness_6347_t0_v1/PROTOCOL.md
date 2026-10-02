# Issue #6347 — infrastructure-speed fairness T0

## H / T / D / C / U

**H.** In a predeclared class of equally authorized, same-priority conflicting intents, first-ready-first-served (FRFS) changes its winner when only compute/transport delay is swapped. A bounded collection window with a predeclared rotating tie right should reduce this delay-swap sensitivity on held-out repeated opportunities without increasing missed deadlines, unsafe/stale admission, or per-principal unfinished work. The null is plausible when arrivals are not near-simultaneous, rights already settle conflicts, or transport delay crosses the collection boundary.

**T.** Freeze a deterministic, no-model event simulator and a separate raw-only auditor. The construction fixture includes equal-origin paired delay swaps, twelve held-out contention opportunities across fixed windows, phase jitter at the close boundary, delayed eligible submission, critical interrupt, shorter-than-window deadline, revoked grant, expired evidence, a disjoint-resource negative control, and an unresolved-rights HOLD. Policies are FRFS, origin-time FIFO, and a five-tick collect-then-rotate rule. The batch opens on the first ready intent, closes at first-ready+5, and admits only intents ready by close; it cannot infer a future/late request from its human-origin timestamp. Every admission revalidates grant and evidence and requires completion strictly before deadline. Critical interrupts and deadlines shorter than the window bypass collection. Missing tie rights yields HOLD. Test only synthetic state; no model, GUI, external task or input.

The primary metric is the fraction of paired runs whose winner changes when only principal-specific compute/transport delay is swapped. Secondary metrics are admitted/on-time count, HOLD/refusal count, per-principal wins, maximum consecutive losses, and unfinished authorized opportunities. Window size and rotation order are fixed before held-out evaluation; no post-hoc tuning. Boundary/strategic-delay scenarios are reported separately and are not excluded from all-attempt denominators.

**D.** `PASS_METHOD_SCOPED` requires exact independent reconstruction of every raw scenario-policy row, planted FRFS sensitivity detected, batch eligibility/deadline/revocation/evidence/conflict gates preserved, explicit HOLD absent rights, and all four output mutation controls rejected. `H_PASS_SCOPED` additionally requires lower batch delay-swap sensitivity than FRFS on the held-out sequence, equal or greater correct on-time effects, no unsafe/stale admission, and no worsening of maximum consecutive losses or unfinished authorized work. Otherwise report the observed FAIL/HOLD; do not tune and rerun this allocation. No result establishes deployed fairness.

**C.** FIFO on human-origin time or an explicit stakeholder decision may be the legitimate policy; windowing can add harmful delay and cannot make heterogeneous tasks exchangeable. If the right to choose is normative and absent, abstention is correct.

**U.** Synthetic clocks do not establish production timestamp accuracy, strategic behavior, human preference, repeated-game value, scheduler interference, or real GUI lease/effect semantics. A fixed test cannot establish fairness across arbitrary distributions.

## Frozen model details

- Synthetic time is integer ticks; `ready = origin + compute_delay + transport_delay`.
- Principal rights are equal. The batch policy rotates a predeclared pointer only among equal-rights intents present at close. Pointer advances only after a successful on-time admission.
- FRFS selects earliest ready time. FIFO selects earliest human-origin time. Ties use stable intent ID only where a policy needs a deterministic outcome.
- A winner must be eligible at admission: grant active, evidence unexpired, resource conflict class valid, and completion time strictly less than its deadline. If all candidates fail, return typed HOLD/REFUSE; no effect is recorded.
- Critical interrupts execute immediately if independently eligible. If any candidate's deadline is shorter than the configured batch interval, that opportunity bypasses batching and uses FRFS.
- A disjoint-resource opportunity is not serialized and both independently eligible intents may proceed.
- Paired fairness probes preserve human-origin timestamps, eligibility, deadlines, resources, rights and scenario identity; only compute/transport delay assignments are swapped.
- The twelve-event held-out sequence is not used to choose the five-tick window or rotation pointer.

## One-shot protocol

1. Construction tests and source/fixture hashes precede allocation.
2. Confirm Issue #6347 has no competing allocation/path and source HEAD equals the preregistered main SHA; verify the pinned local Docker image ID and OrbStack Engine.
3. Run candidate once in a network-disabled, read-only-source, bounded CPU/memory container. Save exact argv, image ID, stdout/stderr, exit status and raw bytes.
4. Only on candidate exit 0, run the independent auditor once in a separate container against raw bytes only. No retries; preserve failure/STOP as the result.
5. Verify hashes and publish all artifacts, boundaries and local CI through a reviewable PR.

