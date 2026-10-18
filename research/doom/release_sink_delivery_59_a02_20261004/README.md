# Release-batch candidate position-ledger validation (Issue #59, A02)

## H / T / D / C / U

**H:** The current #7635 candidate's per-position ledger should preserve the same correct custody classification whether the sink fails before acceptance or accepts then raises, and regardless of whether failure occurs at the head, middle or tail of a three-row batch.

**T:** Frozen current candidate head `1030a47894cb4f30a8c92bd577432e7962560741` from PR #7635; backend blob `9bd000ad5614940f2bd59e3e5e8143b3a29a77b9`, SHA-256 `ec406fc29b2ac1c412d385aac11b58049e1bd761a5dc5dd8123909c6c92c4e70`. Run one failure at positions 0, 1 and 2 for fail-before-accept and accept-then-raise. No candidate retries are added; no candidate source is changed.

**D:** All six ledgers classified earlier rows as `confirmed`, the failing row as `unknown`, and later rows successfully published through incomplete cleanup as `confirmed_incomplete`. Accepted-then-raise rows were never retried. The raw-only auditor passes 6/6.

**C:** Deterministic mocked sink and owner state, invoking the exact candidate implementation loaded from its frozen Git object. No X server, game, model, GUI, OS input, Docker/WSLc or live allocation. This validates synthetic publication custody only, not durable storage or physical release.

**U:** The full executor/session path and a durable consumer of the release ledger were not exercised in this matrix; they have separate focused tests reported by PR #7635. Whether the telemetry consumer persists/reconciles the terminal ledger remains outside this test.

## Reproduction

From a repository clone containing the frozen PR commit:

```sh
python3 probe.py /path/to/agent-interface
python3 audit.py
```

`RAW_STDOUT.txt` is the exact six-case output. The auditor reads only that captured output. Candidate source SHA-256 and Git blob are recorded above. PR #7638's candidate was closed without merge; this package is pinned to the then-current #7635 head instead.
