# A02 T0 formal fixture result

**Disposition: `PASS_FIXTURE_METHOD_SCOPED`.** This is a bounded result for the deterministic synthetic fixture and its independent raw-row audit, not evidence of model behavior.

## Executed gates

- Frozen source and one-shot rules: [`FREEZE.json`](../../FREEZE.json), freeze commit `847332de8b1ce3a7044baf08792384ba5a1e585d`; main base `fc595c0693750e4214d8f02f393b71db64db8894`.
- Candidate CLI: exactly one invocation, exit 0, stdout/stderr empty. It produced 50 rows: 48 matched (3 conditions × 4 depths × 4 arms) plus 2 position controls. The 507,279-byte raw JSON SHA-256 is `fddae0822660244e03dfc9aca8a9807839d22081e2faf3dc72d770dcf4276280`.
- Independent auditor CLI: exactly one invocation, exit 0, `PASS`, 48 matched rows, 2 position rows, zero errors. The 66-byte audit JSON SHA-256 is `6727564a6b867e659e187f88e17acf9521f07d5eab9a720a2a68c0229bc7ffa1`.
- Exact commands, exit codes, stdout/stderr, byte counts, hashes, environment, and invocation counts are in [`FORMAL_RUN_RECORD.json`](FORMAL_RUN_RECORD.json).

## Interpretation and limits

The gate supports only that this authored corpus has the frozen cardinality/strata and byte-level matched-context invariants, and that the separately implemented auditor accepted it. It does not show that a model experiences or avoids proactive interference. Equal UTF-8 bytes and cue offsets do not imply equal tokenization, salience, attention, or meaning. There was no model, tokenizer, GUI, user data, live application, human outcome, task-effect, latency, safety, deployment, or generalization test; no container was used because Issue #8341 authorizes this finite no-model host-only fixture check and makes no isolation claim. T1 remains unauthorized.

The frozen policy was followed: no candidate/auditor retries and no construction tests, imports, or package tests after the first formal candidate invocation. Only read-only artifact/hash checks followed.
