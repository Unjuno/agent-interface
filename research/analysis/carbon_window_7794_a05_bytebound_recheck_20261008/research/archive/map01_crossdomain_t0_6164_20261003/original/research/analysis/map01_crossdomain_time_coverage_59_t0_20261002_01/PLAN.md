# r133 cross-domain time-coverage identifiability T0

Allocation: `R133-CROSSDOMAIN-TIME-COVERAGE-59-T0-20261002-01`

## H / T / D / C / U

- **H:** A common time-weighted “useful control coverage” measure is transferable from the retained DOOM v38/v39 traces to the OpenTTD episode only when every counted actuation has identity-bound physical down/up observations on one clock, an independently scored useful-effect observation joined to the same action/clock, and a compatible denominator. Program envelopes, terminal neutral receipts, and observer-record indices are not substitutes. Applying that gate to the retained traces will likely produce an explicit HOLD rather than an invented number.
- **T:** Read-only reconstruction of six immutable main-branch files: DOOM v38/v39 runtime event streams and posthoc analysis; OpenTTD runtime events, AIT observer log, and posthoc task audit. Parse admissions, per-key/per-button edges, neutral terminal receipts, program envelopes, observer state transitions, effect identity, and available clocks. Candidate and separately authored raw-only auditor each run once after freeze; retries 0. No model, game, GUI, OS input, X server, network service experiment, Docker, WSL, or GPU workload.
- **D:** Candidate returns `HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED` unless every domain has physical per-actuation intervals, a shared action/clock identity for the independent effect, and a comparable denominator. Independent audit must reconstruct source counts and the OpenTTD observer transition from raw; accept the HOLD only if all source hashes match and no unavailable boundary is silently substituted. Construction tests include complete synthetic positive, missing edge, terminal-neutral-only, observer-index-only, and mismatched-clock cases.
- **C:** Source base `279ee4aee96c5646360239409931821726566aa2`, after rechecking each Git blob/SHA-256 at current main. Exact gate semantics, not a numeric coverage estimate, are the transferable object. The candidate’s 13+ second program envelopes, the OpenTTD 7/7 same-program neutral terminal joins, and the independent A→B observer state remain separate measurements.
- **U:** This cannot recover missing physical release timestamps or a shared observer clock from historical records. It does not measure true held duration, first useful feedback latency in DOOM, matched recovery efficacy, task completion, MAP01 exit, safety, speed benefit, or general cross-domain performance. r133 forbids new model/GUI calls, so no new live episode is authorized or used.

## Decision rule and scope

`PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED` means the raw sources support the conservative non-identifiability decision and the independent parser agrees. It is **not** a PASS for the transferable time-coverage hypothesis. Any candidate PASS on incomplete evidence is `FAIL_AUDIT`; source/count/identity mismatch is also `FAIL_AUDIT`. The parent PR #6111 `HOLD_CROSS_DOMAIN_EFFECT_CLOCK_JOIN`, DOOM v38/v39 artifacts, and all original scores remain untouched.

Host CPython standard library is sufficient for these immutable JSON/JSONL/text files. A container is not used because no OS, application, timing, model, or runtime behavior is under test; no shared container slot is reserved or consumed.
