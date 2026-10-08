# Formal execution record — allocation A01

Status: **HOLD_AUDIT_EXECUTION_FAILURE**. This allocation is terminal. Candidate output is retained but is not an independently verified result.

## Receipts

- Runtime: native macOS arm64 host CPU, CPython 3.14 stdlib; no container/OrbStack isolation claim.
- Candidate CLI, invoked once: `python3 candidate.py --input fixture/public.json --out results/formal_01/candidate.raw.jsonl` — exit 0; stdout `candidate_rows=8`.
- Auditor CLI, invoked once: `python3 audit.py --input fixture/public.json --truth fixture/auditor_truth.json --raw results/formal_01/candidate.raw.jsonl --expected-public-sha256 8614e740c5651471c957ece8df6728f10996e4e24ded12ef2eed21fcf90a45b3 --out results/formal_01/audit.json` — exit 1; `RecursionError: maximum recursion depth exceeded`.
- Retries: 0. Do not repair and rerun either frozen formal CLI in this allocation.
- Candidate raw SHA-256: `4e4f95a92add0cc8f19ae7f10725e21905ab81116f7db17847e0abd26fc277d0`.
- Auditor output: absent (exclusive output path was never created).
- Frozen auditor SHA-256: `54dbce5518b059607315fb1c6c489ed1a79588d19237018d263f8316d2ae3df1`.

## Candidate-only observations (not audit-reconciled)

| Case | All-feature squared gap | Layer-relative squared gap | Candidate status |
|---|---:|---:|---|
| target-parallax-positive-1 | 64 | 144 | DISTINGUISHED |
| target-parallax-positive-2 | 361/4 | 121 | DISTINGUISHED |
| foreground-dominance-sham | 784 | 0 | UNKNOWN |
| zero-relative-motion | 0 | 0 | UNKNOWN |
| ambiguous-layer-membership | 49 | unavailable | UNKNOWN |
| stale-track-identity | 49 | unavailable | UNKNOWN |
| invalid-probe-receipt | 49 | unavailable | UNKNOWN |
| insufficient-layer-support | 16 | unavailable | UNKNOWN |

These values describe the retained candidate JSONL only. They do not satisfy the protocol's independent auditor/reconciliation gate, and the two positives must not be advertised as a formal pass.

## Failure analysis

`check()` calls `corruption_controls()`. Each corruption helper `_raises()` calls `check()` again, which starts the same mutation controls recursively. The auditor therefore exhausts recursion depth before completing or writing `audit.json`. The five corruptions were **not** validated; they cannot be counted as rejected. The failed auditor source and candidate raw output are preserved unchanged. A distinct successor allocation must preregister a non-recursive independent auditor/test before any further formal run.

## Construction checks (separate from formal execution)

Before freeze, the first draft fixture was touched by candidate helper calls. That draft was retired; its values are disjoint from the frozen fixture. Final construction tests use separate mini-cases and never read the frozen fixture. Five unittest cases passed; `py_compile`, fixture generation, and `git diff --check` also passed before formal execution. After all formal allocations were terminal, the local batch CI reran only this five-test mini-case suite plus `py_compile`; both passed. No formal candidate or auditor CLI was rerun.
