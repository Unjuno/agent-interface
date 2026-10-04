# Release-batch candidate position-ledger validation (Issue #59, A02)

## H / T / D / C / U

**H:** The #7638 candidate's per-position ledger should preserve the same correct custody classification whether the sink fails before acceptance or accepts then raises, and regardless of whether failure occurs at the head, middle or tail of a three-row batch.

**T:** Frozen candidate head `f7730ad400eb29addcd6a8c747e06c7d79af32fd` from PR #7638; backend blob `5b1d4ef00ad5d6812093c2308eea9677bc6abc5b`, SHA-256 `463bb7f9e15c8b8af30804c9463dd53b8e6f5d327cf1dbffc3ccd7033ff6e77a`. Run one failure at positions 0, 1 and 2 for fail-before-accept and accept-then-raise. No candidate retries are added; no candidate source is changed.

**D:** All six ledgers classified earlier rows as `confirmed`, the failing row as `unknown`, and later rows successfully published through incomplete cleanup as `confirmed_incomplete`. Accepted-then-raise rows were never retried. The raw-only auditor passes 6/6.

**C:** Deterministic mocked sink and owner state, invoking the exact candidate implementation loaded from its frozen Git object. No X server, game, model, GUI, OS input, Docker/WSLc or live allocation. This validates synthetic publication custody only, not durable storage or physical release.

**U:** The full executor/session path and a durable consumer of the release ledger were not exercised in this matrix; they have separate focused tests reported by PR #7638. Whether the telemetry consumer persists/reconciles the terminal ledger remains outside this test.

## Reproduction

From a repository clone containing the frozen PR commit:

```sh
python3 probe.py /path/to/agent-interface
python3 audit.py
```

`RAW_STDOUT.txt` is the exact six-case output. The auditor reads only that captured output. Candidate source SHA-256 and Git blob are recorded above.
