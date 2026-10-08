# Issue #8668 T0 A02 — policy-specific counterfactuals

This is a fresh, CPU-only finite-model allocation after the retained A01 `FAIL_HARNESS`. A01 remains immutable. Its defect was that the candidate computed the canceled plant once and reused that plant for every policy, while the auditor repeated the same counterfactual error. A02 first applies each policy's action to the shared exogenous schedule, derives that policy's own plant outcome, and then computes its claims and retry decision.

## H / T / D / C / U

- **H:** On the frozen finite plant, an optimistic globally-controllable event label can falsely report cancellation after the irreversible `EMITTED` frontier when it sees only cancel-command delivery; a globally-uncontrollable label can miss a safe pre-emission removal opportunity. The phase-refined policy will preserve every confirmed safe removal and will never report cancellation without operation-bound removal proof or admit a duplicate retry.
- **T:** Enumerate all 480 combinations of five cancellation-intent phases, two control delays, two removal-receipt delays, two equal-frontier orderings, two effect/release receipt orderings, three stale-receipt positions, and retry/no-retry, plus one no-input control. Compute four policy-specific trajectories per schedule. A distinct raw-only auditor independently enumerates the same exogenous schedules and recomputes actions, plant outcomes, reports, and retry decisions.
- **D:** `METHOD_PASS_SCOPED` requires exact candidate/oracle agreement, zero phase-refined false cancellation claims and unsafe duplicate retries, preservation of every available safe removal, and rejection of all five frozen corruption controls. The static-comparator contrasts are reported as counts, not generalized to every static supervisor. Any mismatch is `FAIL_HARNESS`.
- **C:** An existing event ledger plus honest UNKNOWN and operation-bound receipts may already provide the required behavior without phase-indexed policy logic. If so, the finite comparator has no runtime implication.
- **U:** The result is only for this authored deterministic model. Real backends may expose different phase boundaries, cancellation receipts, delay bounds, or irreversibility points. No GUI or runtime allocation is authorized or tested.

## Allocation and reproduction

Allocation: `PHASE-CONTROL-DELAYS-8668-T0-A02-20261009`

Base: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`

Branch: `research/8668-phase-control-delays-a02-20261009`

The `FREEZE.json` is the prospective source/protocol freeze. The candidate has one formal invocation; the auditor has one invocation only if the candidate exits 0. Do not rerun either. The `run-01/` directory may exist for shell redirection, but it must be empty before candidate execution.

```sh
cd research/analysis/phase_dependent_controllability_8668_t0_a02_20261009
mkdir run-01
/usr/bin/sandbox-exec -p '(version 1) (deny network*) (allow default)' python3 -B candidate.py > run-01/candidate.json 2> run-01/candidate.stderr
candidate_status=$?
if [ "$candidate_status" -eq 0 ]; then
  /usr/bin/sandbox-exec -p '(version 1) (deny network*) (allow default)' python3 -B auditor.py run-01/candidate.json > run-01/audit.json 2> run-01/auditor.stderr
  auditor_status=$?
else
  auditor_status=SKIPPED_CANDIDATE_EXIT
fi
printf 'candidate=%s auditor=%s\n' "$candidate_status" "$auditor_status"
```

The first outcome, including a nonzero exit, is retained without retry or relabeling. `REPORT.md` records the actual decision and scope after the one-shot run.
