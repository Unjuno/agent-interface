# Issue #6580 T0b — formal allocation report

**Disposition: `PASS_METHOD_SCOPED` for the exact frozen deterministic table only.** This successor evaluates a synthetic `CONTINUE`/`YIELD` rule after allocation 01's set-encoding-only result. It does not bypass the parallel T1 result `HOLD_MODEL_LIFETIME_UNIDENTIFIED` and provides no live-interface evidence.

## Frozen scope and receipts

Allocation `MODEL-AMBIGUITY-DECISION-6580-T0B-20261002-01` was preregistered on Issue #6580 before its formal calls. It crossed three declared lifetimes, two event phases, four evidence states, and two explicit move/observation contracts for 48 decision rows; six parameter-insensitive controls were added. The recorded support cardinalities sum to 116. Runtime was native WSLc 3.0.1.0 using cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, pull/network disabled, one CPU, requested 1G, uid 65534. The exact warning was `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Requested memory is recorded; enforcement is not claimed. No Docker, Podman, GPU, model, GUI, human, authority, or external effect.

- Construction: one invocation, exit 0; 6/6 tests passed and seven frozen mutations were rejected.
- Candidate: one invocation, exit 0; raw SHA-256 `d489ffde3af95c4c032f84295e5be486f1ad779f9de41959098452a411b17ed5`.
- Independent auditor: one invocation, exit 0; `PASS_METHOD_SCOPED`, 48/48 rows, 6/6 controls, 116 support-history instances, six explicit `CONTINUE`-over-unspecified witnesses, 36 point-comparator unsafe-possible rows, zero recorded unsafe gate dispatches, zero errors.

## Interpretation and limitations

For this table, valid same-session FULL evidence narrows support to its recorded theta; ZERO does not carry prior-step evidence forward; EVENT narrows only after the declared event; missing/stale evidence preserves `{0,1}`. In agent-first/reactive rows, the explicit rule continues only on a singleton support; otherwise it yields. This produces the six frozen rows where a justified persistent-model continuation differs from a lifetime-unspecified YIELD. The 36 point-comparator rows indicate only that an unsafe theta remained *possible*; the point comparator was never dispatched and no effect occurred.

The nature-first/public contract contains a coverage limitation: candidate chooses `prior_support[0]` as one representative current theta. The audit checks that emitted branch and does not enumerate both public observations for rows with support `{0,1}`. Thus zero recorded unsafe dispatches is not a universal branch-safety proof. Likewise the game uses stipulated observation semantics and is not a pure order-of-play theorem or a numerical reproduction of the source paper. Full public-branch enumeration is a separate scientifically justified successor; it must not overwrite this allocation.

No real interface transition lifetime, responsive app, safety, task success, probability, latency, token, or product claim follows. T1 remains HOLD until evidence from one declared app/version/session population can distinguish persistence from per-step variation. All raw output, byte-identical audit input, run receipts, exit codes, audit JSON and checksums are retained. No formal stage was retried.
