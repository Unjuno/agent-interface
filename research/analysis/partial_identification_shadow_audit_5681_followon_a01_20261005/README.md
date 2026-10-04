# Partial-identification follow-on for Issue #5681

This is a distinct, CPU-only method construction following the separate finite shadow-estimator T1 STOP recorded in [`selection_aware_shadow_audit_5681_t1_v1/STOP.md`](../selection_aware_shadow_audit_5681_t1_v1/STOP.md). It does not repair, repeat, or promote that allocation. The changed question is whether incomplete binary labels on a **known, complete finite capture frame** support a decision that is robust to every possible assignment of the unknown labels, while explicitly refusing a claim about transitions outside that frame.

## H / T / D / C / U

**H —** With a complete frame of `N` candidate captures, `k` independently confirmed positive labels, and `u` unresolved binary labels, enumerating every completion yields the sharp finite-frame prevalence interval `[k/N, (k+u)/N]`. A threshold decision is robust only when the entire interval is strictly on one side; equality, a missing denominator, or a declared out-of-frame transition must remain on hold.

**T —** Allocation `SELECTION-AWARE-PARTIAL-IDENTIFICATION-5681-T0-20261005-01`; eight frozen finite cases. The candidate uses the closed-form extrema. A separately executed auditor enumerates every binary completion (`2^u`) using exact rational arithmetic and compares the complete output. Cases cover zero-inclusion unknown labels, all-unknown labels, robustly-above and robustly-below thresholds, equality at either interval endpoint, an incomplete frame, and a known transition outside the capture frame. Ten frozen output mutations test the auditor. No model, GUI, network, task input, or production route is invoked.

**D —** `PASS_METHOD_SCOPED` only if all eight candidate outputs equal the independent completion enumeration, all `30` eligible binary completions are counted, the missing-denominator row emits no bounds, the out-of-frame row retains its scoped bounds but returns `HOLD_OUT_OF_FRAME_NOT_IDENTIFIABLE`, threshold equality holds, action authority remains `NONE`, effect/safety remains `NOT_EVALUATED`, and all ten corruptions reject. Any contradiction is `FAIL_METHOD`; incomplete provenance, output, or audit is `HOLD`.

**C —** If all semantic labels are actually available, a full census is simpler than partial identification. If audit inclusion has positive probability, a separately designed, fully executed random audit may provide design-based information, but that is outside this construction. An arbitrary assumption about unknown labels could narrow the interval but is not part of this test.

**U —** This establishes arithmetic only for a fully enumerated, fixed finite capture population with binary labels and exact label semantics. The threshold is a fixture parameter, not a safety policy. It gives no confidence interval, GUI prevalence, duration, between-capture or hidden-state bound, task effect, action safety, O3/O4 adoption rule, or runtime authorization. Unknown-label intervals ignore inclusion probabilities except to record zero-support units; no missing-at-random assumption is used.

## Finite model

| Symbol | Meaning | SI unit / type | Domain and assumptions |
|---|---|---|---|
| `N` | Rows in the complete captured-candidate frame | count, dimensionless `1`; integer | `N > 0`; rows are unique candidate captures |
| `k` | Confirmed positive labels among the `N` rows | count, dimensionless `1`; integer | `0 ≤ k ≤ N` |
| `u` | Unknown labels among the `N` rows | count, dimensionless `1`; integer | `0 ≤ u ≤ N-k` |
| `τ` | Frozen maximum prevalence threshold | dimensionless proportion `1`; exact rational | `0 ≤ τ ≤ 1`; equality is HOLD |
| `L` | Lower finite-frame prevalence bound | dimensionless proportion `1`; exact rational | `L = k/N` when the frame is complete |
| `U` | Upper finite-frame prevalence bound | dimensionless proportion `1`; exact rational | `U = (k+u)/N` when the frame is complete |
| `πᵢ` | Declared audit-inclusion probability for candidate `i` | dimensionless probability `1`; exact rational | `0 ≤ πᵢ ≤ 1`; does not identify a still-unknown label in this record |

If `capture_frame_complete=false`, `N` is not the population denominator and the candidate emits `bounds=null`. If a transition is known to be outside the frame, `[L,U]` remains only a captured-frame interval while the broader claim is `HOLD_OUT_OF_FRAME_NOT_IDENTIFIABLE`; the outside transition is never inserted into `N`.

For a frozen decision threshold `τ`: classify `ROBUST_ABOVE_THRESHOLD` only if `L > τ`, `ROBUST_BELOW_THRESHOLD` only if `U < τ`, and otherwise HOLD. If either endpoint equals `τ`, use `HOLD_TOUCHES_THRESHOLD`. These are numeric method classifications only: `action_authority=NONE` and `effect_safety_gate=NOT_EVALUATED` in every row.

## Reproduction

The frozen candidate command is `python -B /src/candidate.py /src/cases.json /out/candidate.json`; the frozen auditor command is `python -B /src/audit.py /src/cases.json /out/candidate.json`. They run in separate WSLc containers with the pinned local image, no network, a read-only source mount and a distinct writable output mount. Exact commands, outputs, exit codes, platform and hashes are in `results/SELECTION-AWARE-PARTIAL-IDENTIFICATION-5681-T0-20261005-01/`.
