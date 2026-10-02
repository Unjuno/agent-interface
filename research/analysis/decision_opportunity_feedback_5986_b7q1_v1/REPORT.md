# Issue #5986 — decision-opportunity feedback T0 result

## Disposition

**`METHOD_PASS_SCOPED`** for the six-case synthetic measurement-method fixture only.

- Frozen candidate: one invocation, exit 0.
- Separate raw-only auditor: one invocation, exit 0; six rows independently reconstructed, zero errors.
- Five effective output corruptions rejected: synthetic-to-verified promotion, invented post-deadline decision window, undelivered-cue promotion, stale-generation acceptance, and erasure of the mandatory-safety refusal.
- All six labels matched the frozen taxonomy; zero `verified_value_claim=true` fields.
- Construction suite: 8/8 passed before the formal invocation.
- Retries, replacement runs, tuning, GPU/CUDA, Docker containers, WSL guest, model/provider, GUI, user input, and network calls: 0.

## Observed finite-fixture distinctions

The capture-only comparator marked cues as captured before deadline even when they were delivered after the last eligible decision, never delivered, or stale. The relevance-only comparator likewise does not account for delivery, current generation, or the decision window. The full taxonomy separated:

| Frozen case | Classification |
| --- | --- |
| Early delivery changes an eligible synthetic choice | `DECISION_RELEVANT_CANDIDATE` |
| Same cue delivered after the final decision | `DELIVERED_BUT_NO_DECISION_WINDOW` |
| Captured early but not delivered | `EARLY_BUT_NOT_DELIVERED` |
| Timely but redundant cue | `NOOP_OR_REDUNDANT` |
| Old-generation cue | `STALE_OR_MISLEADING_YIELD` |
| Mandatory safety cue with a withholding request | `MANDATORY_SAFETY_CUE_INELIGIBLE_FOR_WITHHOLDING` |

The first case's authored counterfactual exact-effect delta is diagnostic fixture data only. The candidate and auditor deliberately label it a **candidate**, never verified empirical value. In the mandatory-safety case all arms still receive the cue; the synthetic withholding request is refused, not executed.

## Reproduction and evidence

Allocation `DECISION-OPPORTUNITY-5986-T0-20261002-01`; owner/task `01a0b990-3d17-72f1-a908-9a2072104ce5`; intake main `3adec9cdc2cff5ef68f19acd55c5823fcaad26df`; frozen branch `research/decision-opportunity-feedback-5986-t0-20261002-b7q1`.

Exact formal command: `python run_once.py` (CPython 3.11.9, Windows host). `RUN.json`, candidate/audit JSON, stdout/stderr and source/input hashes are in `outputs/DECISION-OPPORTUNITY-5986-T0-20261002-01/`. Candidate wall time 0.078 s; auditor 0.078 s. Read-only Docker inventory query timed out at 5 s; host-only execution neither assumed an empty container set nor touched Docker.

Raw SHA-256:

- Candidate JSON: `C3023018F657E33C4D6A9BF70A956BFA030B04FDDE32671A096E1D0A02A51A2F`
- Auditor JSON: `19F05F1C9CBC0005B330D768D15212D0D338D6051E05D8C090E75898B12A73BC`
- Run receipt: `E68602D2F0B7FDFAC25E7AEB2F08A4D185B46E8B68438771B3AB82A14B7B3C64`
- Freeze manifest: `16736D9CD587B20F4EB985689BAA27A06701DCF9BC628E1B8515ED12D91CC680`

## H / T / D / C / U and scope

This is a finite synthetic **taxonomy/accounting** result. It shows the fixture's declared distinctions are operationally testable and independently reconstructed; it does not establish that early feedback helps a real bounded agent, improves human continuation, changes real route decisions, improves a GUI effect, or is safe in an application. It does not test the existing main-branch host feedback API. A real value claim needs a new, prospective, matched disposable-app experiment with an independent effect oracle. Full goal remains open.
