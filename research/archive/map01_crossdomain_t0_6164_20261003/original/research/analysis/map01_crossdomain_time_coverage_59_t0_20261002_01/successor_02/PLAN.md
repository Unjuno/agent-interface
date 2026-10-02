# r133 cross-domain time-coverage successor T0-02

Allocation: `R133-CROSSDOMAIN-TIME-COVERAGE-59-T0-20261002-02`.

## H / T / D / C / U

- **H:** Time-weighted useful-control coverage remains unidentified across DOOM and OpenTTD unless identity-bound physical down/up intervals, same-clock independently useful effects, and a compatible denominator exist in each domain. T0-01's conservative HOLD is plausible, but its auditor fixture and candidate observer-count field failed audit.
- **T:** New one-shot deterministic raw replay against the six immutable inputs from T0-01. Reuse the predecessor's unchanged trace classifier; normalize the candidate observer counts in this allocation only. A separately authored raw-only auditor recomputes full event counts, terminal joins, observer states/transitions and source hashes, then compares every published count/status. Candidate once, auditor once, retries zero. Host standard library only; no runtime, model, GUI, input, game, Docker, WSL, or GPU.
- **D:** `PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED` only if v38 score count is 1; candidate event-count maps equal independently reconstructed raw counts; the observer record count is 263 while transition witnesses are 1 at index 91; all per-domain and cross-domain coverage remain HOLD; source hashes match; malformed candidate-count/status controls reject.
- **C:** Predecessor T0-01 remains unchanged at PR #6164. Its v38 `post_control_score=1` and current-main input hashes are retained. Exact predecessor candidate source SHA is recorded in the new freeze. Inputs are referenced from the parent package and revalidated against the new freeze.
- **U:** A successful audit validates only historical record classification and conservative non-identifiability. No new physical occupancy, useful-feedback timing, matched recovery benefit, human tempo, task completion, safety, or MAP01 exit is measured.

## Decision and execution policy

This is a distinct allocation/output path. Never rerun or rewrite T0-01. The candidate is the unchanged predecessor classifier plus a separately frozen output-normalization wrapper; the raw auditor imports no candidate code. If candidate or auditor fails, preserve both outputs and stop without retries.
