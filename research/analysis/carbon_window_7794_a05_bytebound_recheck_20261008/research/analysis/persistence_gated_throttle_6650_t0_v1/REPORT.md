# T0 formal result — Issue #6650

Allocation: `PERSISTENCE-GATED-OPTIONAL-THROTTLE-6650-T0-20261002-01`

Decision: **FAIL_HYPOTHESIS** (frozen candidate-vs-queue-length criterion not met); raw accounting controls passed, but the controller-law audit is incomplete.

Scope: synthetic finite discrete-event method experiment only; host-local CPython 3.14.5, no OrbStack container.

## Frozen protocol and execution

The experiment used nine fixed exogenous traces and 63 offered IDs. Candidate, fixture, auditor and construction tests were hashed in `FREEZE.json` before the single formal candidate execution. A single independent raw-only audit followed. The pre-freeze exploratory probe and its adverse comparison were disclosed in the preregistration and freeze record; thresholds and fixture were not changed after the probe. `RUN.json` records exact commands, exits and output hashes. `SHA256SUMS` covers the preserved bundle.

Construction checks: 8/8 passed. Independent raw accounting audit: 0 errors. The auditor reconstructed all offered IDs, suppressions, service records, source generations, enqueue-to-service-start sojourns, freshness terminals and mandatory coverage from fixture and event rows. Seven corruption controls were rejected by the construction suite. This auditor did **not** independently replay the full controller law from state observations; state-transition counts below are a separate raw-state descriptive reconstruction and are not a controller-law audit.

## Primary result

| Frozen trace | Fixed stale optional deliveries | Queue-length | Age-persistence | Age suppression | Interpretation |
|---|---:|---:|---:|---:|---|
| sustained_overload | 13 | 3 | 6 | 7 | Both controls improve over fixed generation; age loses to queue-length by 3 stale deliveries, failing the preregistered noninferiority clause. |
| transient_burst | 0 | 0 | 0 | 0 | Age-persistence had no tier transition or suppression; queue-length suppressed one optional offer. |
| zero_dequeue_blackout | 0 | 0 | 0 | 1 | Age entered throttling with zero completed optional sojourn samples at its first transition; this is a distinct signal-availability property, not a freshness win. |
| semantic_invalidation | 2 | 2 | 2 | 1 | Age suppressed one invalid-generation request, but two deadline-stale deliveries remained. |

The Issue's original transition-efficiency expectation also points the wrong way in this frozen synthetic bundle. Reconstructing tier changes directly from consecutive per-session raw `states` rows gives 16 age-persistence transitions versus 11 queue-length transitions across the nine traces. This is descriptive transition activity (not a preregistered formal gate, and not an independent replay of the control law); it does not support a claim of fewer oscillatory transitions. In the sustained-overload trace alone, age has 2 transitions versus queue-length's 4, but that local slice cannot override the all-trace result or the stale-delivery regression.

Across every trace, mandatory IDs and their terminal outcomes exactly matched fixed generation for queue-length, age-persistence and oracle diagnostic. Stale-feedback and unknown-optionality/scope traces failed open (no candidate suppression); all offered IDs remained represented. The oracle is an upper-bound diagnostic only and not an implementable comparator.

## Decision and limits

The preregistered T0 required age-persistence to improve on fixed generation **and** be no worse than the matched queue-length controller on the frozen overload trace. It improved 13→6 but queue-length reached 3, so the composite T0 hypothesis is **FAIL_HYPOTHESIS**. The Issue's stricter original expectation (fewer stale deliveries and fewer oscillatory transitions than queue-length) is likewise unsupported: stale is 6 vs 3 and descriptive state transitions are 16 vs 11. No retuning or post-result successor claim is made here. A later distinct Issue may preregister a different question, such as whether age is useful specifically when service-completion feedback disappears, but this T0 does not establish production utility.

The simulator has deterministic synthetic arrivals, one simplified FIFO service facility per trace, exogenous offered opportunities, fixed freshness deadlines and a simplified controller. It does not measure real queues, planner decisions, task correctness, user benefit, latency, resource cost, shared-service interactions, endogenous demand, or safety. The raw identity/freshness/mandatory controls passed; full independent validation of candidate transition-law conformance did not exist in this T0. Therefore this is a reproducible adverse synthetic comparison, not a blanket method PASS and not evidence to deploy a throttle. No control pass authorizes suppression of unique evidence, mandatory controls, or real work.

## Local delivery validation

After rebasing onto current main `20896908089b52db95678626b295219012769627`, local delivery checks passed: Analysis Index **502/502**; the focused T0 suite **8/8**; all 15 suites in the current Analysis Index workflow **90/90**; workspace-index unit tests **21/21**; committed-tree workspace index **156 namespaces**; Public Navigation **26 documents / 1,456 repository-relative links**; `py_compile`; and all artifact SHA256 checks. The geometry-feasibility suite initially had 2/10 local setup failures because it expects the workflow snapshot that CI restores before testing. Confirming that snapshot's pinned SHA and emulating only its file read in memory made the exact suite pass 10/10; no tracked workflow file was altered. The canonical latest-main index refresh also reconciled an existing generated-block annotation/order drift while adding this result. The preregistration remains byte-identical to its pre-run freeze; consequently unfiltered `git diff --check` flags only its intentional Markdown hard-break spaces. All other changed paths pass the whitespace check. Hosted PR Actions remain a separate integration gate.
