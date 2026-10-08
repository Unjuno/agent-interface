# Issue #6367 T0 — exposed-success ledger method result

**Disposition: `PASS_METHOD_ONLY`.** The finite event-ledger method preserved every exogenously assigned opportunity, rejected outcome credit from stale or unmatched evidence, and prevented a post-policy-selected success subset from replacing the all-offer contrast. This is not evidence that local adaptation improves real task success.

## H / T / D / C / U

- **H:** An all-offer policy-assignment denominator avoids making a null all-offer result look beneficial merely because the analysis conditions on post-policy adaptation.
- **T:** One frozen, deterministic CPU candidate processed two JSON fixtures: eight primary opportunities (planted benefit, null, response suppression, shifted challenge, stale cue, missing independent effect, missing qualified occupancy, and unsafe release) plus four matched selection-trap opportunities. A separately implemented standard-library auditor reconstructed each row from the raw fixture bytes.
- **D:** The construction gate required the selection trap to remain null across all four offers in both arms (2/4 vs 2/4), even though the two adaptive-triggered successes were both successful (2/2); the primary fixture had to fail closed on the planted release/safety violation; the auditor had to match candidate classifications, denominators and decisions, and reject the frozen mutation controls. All gates passed.
- **C:** These are stipulated records, not observations from an external challenge generator. The experiment does not validate whether real policies preserve comparable exposure, whether the independent-effect oracle is adequate, or whether physical occupancy can be measured with this receipt schema.
- **U:** No causal, live-control, runtime, statistical, safety-rate, user-benefit, latency, memory, or product inference. The T2 empirical hypothesis remains untested. Post-policy trigger/occupancy fields are descriptive only.

## Formal execution

Frozen base main was `c6e4c7ad413bcc9605ab5bf00df0eaa4ac7ba560`; the exact source/input freeze is commit `3b00b142dde0b408c585552b2649fab4bb7fadc7`. The candidate ran once, exit 0, no retry. The raw-only auditor ran once after candidate success, exit 0, no retry, with `PASS_METHOD_ONLY` and zero errors. Exact commands, stdout and environment are in [RUN.json](RUN.json); source/input hashes are in [FREEZE_SHA256SUMS](FREEZE_SHA256SUMS).

| Fixture | Fixed arm | Adaptive arm | Candidate disposition |
| --- | ---: | ---: | --- |
| Primary controls (8 assigned each) | 3 verified successes, 5 non-successes | 2 verified successes, 1 non-success, 4 unknown, 1 safety failure | `FAIL_SAFETY` because the planted unsafe release is a hard stop; unknowns are not scored as zero |
| Post-policy selection trap (4 assigned each) | 2/4 = 0.50 | 2/4 = 0.50 | `NULL_ALL_OFFER_EFFECT`; the descriptive selected subset is 2/2 successful adaptive triggers |

The unsafe synthetic row is an intentional challenge to the method. Returning `FAIL_SAFETY` is the expected correct behavior, not a measured system incident. The shifted-challenge row is `UNKNOWN_NONCOMPARABLE_CHALLENGE`; stale-trigger provenance is invalid; missing independent effect and physical-occupancy evidence remain unknown. The auditor independently confirmed the two denominators (8/8 and 4/4), decisions, and frozen input SHA-256 values.

## Construction, audit and environment

The 12 focused tests passed normally and under `python -O`; mutation controls reject a hidden scheduled offer, changed source generation, changed release label, and altered candidate summary. A separate test rejects booleans masquerading as physical timestamps. `research/check_workspace_index.py` passed (154 top-level namespaces); final `check_public_navigation.py` passed (26 documents / 1,241 links); the analysis index check passed (378 retained directories); and `git diff --check` passed. The first post-run navigation check ran before the new result files were staged and correctly reported their referenced targets as not yet tracked; after staging, the full 1,241-link check passed. Earlier test-first REDs and command-construction errors are retained in [CONSTRUCTION.md](CONSTRUCTION.md); they were construction/packaging events, not candidate retries.

The run used Ubuntu 24.04.4 / Python 3.12.3 / WSL2 kernel `6.18.40.1-microsoft-standard-WSL2`. It used no WSLc container because the fixture has no isolation/service dependency and another WSLc lane had been active during planning; no Docker Desktop, model, GUI, user input, GPU or network was used. Peak memory and speed were not measured.

## Result integrity and next boundary

Frozen source and fixtures remain unchanged after the formal call. Candidate outputs are in `results/`; the independent audit is `results/audit.json`; exact stdout/exit receipts are retained alongside them. [SHA256SUMS](SHA256SUMS) binds the complete retained package.

This closes only the #6367 T0 method gate. It does **not** qualify a T2 adaptation benefit, close Issue #59's live threat-control requirement, or authorize a real GUI/MAP01 allocation. The next eligible step is the separately described read-only T1 audit of retained #59 traces for complete exogenous challenge coverage, source-bound trigger/response, qualified physical occupancy and independent useful-effect/deadline evidence; if those joins are absent, retain `HOLD_RETROSPECTIVE_ONLY`.
