# Issue #7059 — verdict-free redundancy disclosure ledger T0

## Disposition

`PASS_METHOD_SCOPED` for an authored measurement-ledger fixture only. The candidate retains event/context records and the raw-only auditor distinguishes five preregistered ledger patterns while rejecting six integrity mutations. No model or human behavior was sampled. Issue #7059's roster-disclosure hypothesis remains untested.

## Question and fixed boundary

The T0 question is whether a first-pass ledger can retain exact request contexts and tool events, fix the actual two-reviewer topology and downstream reducer, prove that no peer content was visible before each first-pass commitment, and keep independent outcome truth out of candidate input. The only authored contrast is omission versus truthful disclosure of the already-existing second reviewer. Individual-accounting text, reviewer count, per-reviewer request cap, evidence pool, required sources and reducer ID are held fixed.

The five preregistered records cover: (1) no measurable change; (2) fewer checks with a missed fault; (3) fewer checks with unchanged correctness; (4) correct `UNKNOWN` retention; and (5) a missing tool event. Two isolated reviewer records are present in every condition. Request contexts are retained byte-for-byte with SHA-256, each event joins to a request by ID/context hash/source, event order precedes commit, and peer-verdict release follows both commits. Truth labels and expected ledger classes are in `auditor_truth.json`, separate from candidate input.

The candidate only projects observable ledgers. It does not infer effort, motivation, hidden reasoning or causal effect. `audit.py` independently reconstructs all rows and uses separately authored calculations; it does not import `candidate.py`. Six in-memory mutations test missing tool log, peer-content exposure before commit, duplicate reviewer topology, context tampering, event-order violation and peer-content release before commit.

## Formal disposition

`PASS_METHOD_SCOPED` requires exact raw reconstruction, all five expected authored classifications, fixed topology/evidence/budget/reducer, valid context and request-event joins, no precommit peer exposure, and rejection of every mutation. An incomplete event log must produce HOLD and cannot be counted as a successful negative check. These are measurement-contract checks on invented rows, not observations from live reviewers.

## Execution

Run from this directory, in order:

```sh
python3 -B candidate.py --input formal_input.json --output formal_output.json
python3 -B audit.py
```

Each formal CLI was invoked exactly once after `FROZEN.json` was written. Candidate/auditor retries: zero. This ran with CPython on macOS arm64 using only the standard library; no container, model, GUI, network, user data or external effect was used. `terminal.json` preserves runtime and artifact hashes.

## Limits and handoff

This T0 says nothing about whether a language model responds to the roster disclosure, whether fewer queries harm real detection, whether the authored truth rule matches a real interface-effect contract, or whether the future experiment has adequate power. It does not measure prompt paraphrase instability, real tool capture, natural fault prevalence, model settings, or participant preference. A later T1 needs its own exact prompt/deck freeze, all-attempt model-call receipts and arm-blind independent source/effect scorer; no such allocation was made here. No T1/T2 claim or runtime change follows.

Base and all source/input digests are recorded in `FROZEN.json`. Historical Issue #5941 results and any prior allocations remain unchanged.
