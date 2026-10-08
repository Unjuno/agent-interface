# Issue #7993 T0 A01 — outcome maturity and verifier-risk claims

Status: **construction passed; formal T0 not yet executed**. This is a finite synthetic method-validation
allocation. It does not modify #5315, #6129, #6208, #2279, or their evidence.
Initial source base: `09964d54e7e6ea7d0b396a2e08438e0f79cd643f`; branch rebased
without conflicts onto main `569c0ac98c8ebec453ddd269273c9b6caaadcb3b` before freeze.

## H / T / D / C / U

### H — hypothesis

For the binary endpoint `verifier_claim_contradicted_by_final_oracle`, a
complete-case risk fraction can appear below a frozen 0.10 threshold while the
full assigned cohort's risk exceeds it if erroneous claims resolve later than
correct ones. The exact all-assigned interval, treating every unresolved row as
unknown, will contain the full-cohort risk and will not issue that unsupported
claim. With a known, verified outcome-independent follow-up design and strictly
positive resolution probabilities, the Horvitz–Thompson risk **point estimate**
will be design-unbiased over a complete finite enumeration of follow-up masks.
This point-estimator property is not a confidence bound, coverage guarantee,
or authority to replace the all-assigned interval.

### T — protocol

- One deterministic, source-frozen finite synthetic fixture; no model, GUI,
  application, user data, rejected proposal, counterfactual effect, or live
  action.
- Binary loss is 1 only when the final independent oracle contradicts the
  narrow verifier claim; 0 means it does not. The oracle is visible only to the
  separate auditor. Candidate input contains only information available at
  each named checkpoint; unresolved rows carry no loss label.
- Freeze calibration threshold `alpha = 1/10` and compare:
  1. `COMPLETE_CASE`: resolved-label loss fraction; diagnostic comparator only.
  2. `ALL_ASSIGNED_BOUNDS`: `[resolved_errors/N,
     (resolved_errors + unresolved)/N]` with every assigned row retained.
  3. `CENSOR_MODEL_ELIGIBLE`: the finite-cohort Horvitz–Thompson point
     estimate `sum(resolved_loss_i / pi_i)/N`, only when the censor model is
     declared known, outcome-independent, and has `pi_i > 0` for every
     assigned stratum. It must never be presented as an upper bound or risk
     certificate.
- Enumerate all 16 independent Bernoulli follow-up masks for a fixed four-row
  cohort with one error, three correct labels, and `pi=1/2` for each row. Include
  all-resolved and zero-resolved controls; informative-delay and hidden
  informative-misspecification witnesses; a zero-support stratum; delayed then
  eventually resolved labels; a row still pending at horizon; a safe terminal
  stop; and permanent loss-to-follow-up with unknown cause.
- A safe terminal stop and permanent loss remain distinct typed unknowns; they
  are neither negative labels nor ordinary administrative censoring. The
  candidate reads only `candidate_input.json`; `oracle_input.json` is mounted
  for the auditor only.
- Run candidate and an independently implemented raw-only auditor in one
  disposable WSLc container invocation. Use the already cached, digest-pinned
  `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
  (`linux/amd64`, Python 3.12.14), `--pull never`, `--network none`, one CPU,
  requested memory 512 MiB, a read-only source mount, and a separate writable
  result mount. Keep the kernel's swap/cgroup warning, if emitted; an accepted
  limit flag is not evidence of effective enforcement.

### D — frozen gates

`PASS_METHOD_SCOPED` only if source/input/run receipts reconcile; the auditor
checks every frozen snapshot and all 16 masks; every all-assigned interval
contains its oracle's full-cohort risk; the informative-delay witness has
complete-case risk 0 below alpha while exact cohort risk is 1/4 and the
all-assigned upper bound refuses the claim; the eligible estimator's exact
mean over the 16 equiprobable masks is 1/4 for the 1/4-risk cohort; and
unverified assumptions, zero-probability support, safe terminal stop, and
unknown-cause permanent loss do not receive a censor-adjusted estimate.
Neither estimator nor output may claim finite-sample coverage from the
Horvitz–Thompson expectation identity. The hidden informative-misspecification
witness must be explicitly adjudicated as non-identifiable from the observed
checkpoint, not counted as a detectable pass.

`FAIL_METHOD` for a false all-assigned bound, look-ahead, dropped assigned row,
safe-stop/loss conflation, incorrect exact expectation, or a risk certificate
derived from a point estimate. `HOLD` for ambiguous endpoint identity, process
receipt, input separation, or independent audit. Report `NO_INCREMENTAL_VALUE`
if the frozen fixture yields no valid decision distinction beyond the
all-assigned bound. No outcome permits live calibration or runtime policy.

### C — alternatives

Fixed-horizon all-assigned scoring may be sufficient and simpler. Follow-up can
be independent in a qualified workload, making the complete-case estimator
reasonable under stronger assumptions. A censor-adjusted point estimate can
be highly variable or misleading when the assumed observation model is false;
an unknown informative-censoring mechanism is not identified from resolved
rows alone.

### U — limits

Four-row authored cohorts and finite masks do not establish production verifier
risk, calibration under shift, validity of real censoring models, survival or
conformal guarantees, application effects, safety, or action authority. The
estimator is a design-based expectation result only under the declared
synthetic mechanism. No independent human review is implied by separate code.

## Ownership and environment preflight (2026-10-05)

- Issue #7993 is open; bounded branch and PR searches for `7993` returned no
  matching branch or PR, and the Issue has no comments/assignee in the fetched
  snapshot. Existing predecessor outcomes remain untouched.
- Dedicated local branch: `research/7993-outcome-maturity-a01-20261005`.
  Worktree path: `C:\Users\junny\Documents\Codex\m7993`.
- WSLc reports `3.0.1.0`. `wslc image inspect python:3.12-slim` identified
  image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`,
  RepoDigest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`,
  linux/amd64, Python 3.12.14. `wslc container list --all` returned four
  historical containers, all `Exited`; none was removed.
- Two pre-freeze container construction tests: Attempt 01 failed one ineffective
  mutation control (four of five tests passed); the mutation was corrected and
  Attempt 02 passed all five tests and ten effective mutations. Both outputs,
  commands, hashes and the WSL kernel memory-limit warning are preserved in
  `CONSTRUCTION_LOG.md`; neither ran candidate/auditor or produced a scientific
  disposition.
- Latest construction-phase host snapshot showed about 3.6 GiB free physical
  memory. Recheck memory and disk immediately before formal invocation.
- The earlier Issue #7889 WSLc test was a different preflight-deviated run;
  its lost session is not input or evidence for this allocation and will not be
  restarted.
