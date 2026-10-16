# Issue #8341 / #5947 T0 A02 protocol

Allocation: `5947-MULTI-UPDATE-PROVENANCE-T0-A02-20261008`  
Successor Issue: [#8341](https://github.com/Unjuno/agent-interface/issues/8341)  
Parent hypothesis: [#5947](https://github.com/Unjuno/agent-interface/issues/5947)  
Predecessor: #8313 A01, whose `HOLD_AUDITOR_COVERAGE`, unsupported-query omission, post-formal construction calls and duplicate-allocation STOP remain immutable. A02 does not pool, repair, replace or reinterpret A01.

## H / T / D / C / U

**H — fixture method only.** A deterministic generator and separately implemented raw-row auditor will verify 48 matched rows (3 query conditions × 4 conflict depths × 4 arms) and a separate 2-row position control. Within each matched condition×depth stratum, all arms preserve exact task/query bytes, complete baseline bytes and source identity, current bytes/source, authority, cue position, exact serialized prefix and suffix, and a fixed 2048-byte history slot. Only slot content varies by arm. Supported current-value and baseline-change queries have explicit authored outcomes; unsupported query has `UNKNOWN_UNSUPPORTED`, null answer and a reason.

**T — host-only CPU construction/formal fixture method.** Host-only standard-library analysis is explicitly authorized by #8341; no isolation claim is made. Runtime: macOS Darwin 27.0.0, arm64, Python 3.14.5, 10 logical CPUs, 68,719,476,736 bytes reported host memory. No model, tokenizer, network, GUI, application, user data or container is required/used. Branch `research/5947-matched-context-t0-a02-20261008`; additive path `research/analysis/proactive_interference_5947_t0_a02_20261008/`. Construction suite must run before freeze. Formal commands, each permitted exactly once:
```sh
python3 -B research/analysis/proactive_interference_5947_t0_a02_20261008/candidate.py research/analysis/proactive_interference_5947_t0_a02_20261008/results/formal/candidate.json
python3 -B research/analysis/proactive_interference_5947_t0_a02_20261008/auditor.py research/analysis/proactive_interference_5947_t0_a02_20261008/results/formal/candidate.json research/analysis/proactive_interference_5947_t0_a02_20261008/results/formal/auditor.json
```
The auditor command is permitted only after candidate exits 0 and candidate output exists and is nonempty. Both outputs must be absent before the first command. Each command's stdout, stderr, exit code, output bytes and SHA-256 are retained. No candidate/auditor imports, CLI calls, mutation tests, construction suite, or other package test may run after the candidate CLI begins. Post-formal operations are read-only hash/readback/index checks only.

**D — `PASS_FIXTURE_METHOD_SCOPED` only if** the candidate exits 0 once, creates exactly 50 valid rows; the independent auditor exits 0 once and returns PASS with 48 matched and 2 position rows and no errors; all strata/arms/depths, query/task/current/baseline/source/authority identities, exact common bytes, fixed history slot and equal full context byte budgets hold; the current cue offset is fixed within matched groups and only the separate position control changes its designated offset; history-required baseline is retained in every arm; unsupported answers stay UNKNOWN; source-linked inferred history remains labelled INFERRED; and all 8 frozen mutation controls are rejected by construction tests and the auditor CLI. Any missing/occupied output, source-hash mismatch, nonzero exit, malformed/missing artifact, unexpected count or gate disagreement is first STOP/FAIL/HOLD; preserve it and do not rerun or repair this allocation.

**C —** Equal UTF-8 serialization length and cue offset do not equalize tokenizer behavior, salience, attention or semantics. Authored synthetic values may not model natural GUI histories.

**U —** No model-facing proactive interference result, tokenizer/attention result, human outcome, GUI/task effect, latency, adaptation, safety, deployment or generalization. T1/model study is not authorized by this protocol.

## Construction and validation completed before freeze

The test-first construction suite has seven tests. It covers 50/48/2 cardinality; full stratum membership; serialized prefix/slot/suffix reconstruction; baseline/source/current identity; explicit UNKNOWN; position-only cue offset; independent audit; eight corruptions (including removal of a serialized history episode while keeping common bytes consistent); CLI pass/fail; and occupied-output refusal. It is construction evidence, not formal result.

Repository checks: `python3 research/analysis/check_index.py`, `python3 -m unittest research.analysis.test_check_index -v`, `python3 research/check_workspace_index.py`, and from `research/`, `python3 -m unittest test_check_workspace_index -v`. These indexes are navigation checks, not scientific gates.

See `FREEZE.json` for exact source SHA-256 values, GitHub blob identities, construction result, formal invocation counters at freeze, base and branch heads, commands and stop rules.
