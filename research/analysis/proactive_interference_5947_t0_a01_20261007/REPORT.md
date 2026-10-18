# Issue #8313 — matched-context integrity T0 A01

**Disposition: `HOLD_AUDITOR_COVERAGE`.** The post-freeze candidate ran once and the separately implemented raw-only auditor ran once with zero retries. Its raw result was `PASS` with zero errors across 32 matched arm records (4 history depths × 2 query types × 4 arms) and four position-control records. The auditor checks equal UTF-8 byte counts and current-cue offsets within strata, and all four pre-freeze corruption controls were rejected, including after refreshing affected manifest hashes. A post-run gate review found that it does not verify the complete baseline evidence record (including its source identity) is equal across arms, or directly compare the serialized bytes outside the history slot. The issue's full matched-context claim therefore remains unproven. This gap is retained; the allocation was not repaired or rerun.

The allocation was host-only on Python 3.14.5 using the standard library. It used no model, tokenizer, GUI, user data, network, live application, action, or container. The candidate's full arm/context manifest and authored expected-information labels are in `manifest.json`; raw arm bytes are in `raw/`. The exact pre-call freeze is `FREEZE.json`; the run record is `FORMAL_RUN.json`.

The candidate fixture and listed controls are retained, but this allocation does not pass its declared method gate because the frozen auditor omits two required equality checks. Do not describe it as evidence that the matched-context fixture is fully validated. It does not show proactive interference, model-facing equivalence, tokenization or attention equivalence, GUI behavior, accuracy, latency, task effect, or safety. Equal byte length and cue position may not equalize tokens, salience, or attention. The parent Issue #5947 remains an unverified hypothesis; its earlier FAIL_SAFETY/HOLD evidence is unchanged. No T1 or model call is authorized by this T0.

## Reproduction and retained results

- Construction tests (before freeze): `python3 research/analysis/proactive_interference_5947_t0_a01_20261007/test_construction.py` — 5 passed, 0 failed.
- Candidate (after freeze): `python3 research/analysis/proactive_interference_5947_t0_a01_20261007/generate.py` — one invocation, exit 0.
- Independent auditor (after freeze): `python3 research/analysis/proactive_interference_5947_t0_a01_20261007/audit.py` — one invocation, exit 0, `PASS`, zero errors.

The source/base, full protocol, generator, auditor, manifest, every raw byte file, and their SHA-256 values are bound in `FREEZE.json`. The post-run coverage review is in `POSTRUN_REVIEW.md`. See [Issue #8313](https://github.com/Unjuno/agent-interface/issues/8313) and parent [Issue #5947](https://github.com/Unjuno/agent-interface/issues/5947).
