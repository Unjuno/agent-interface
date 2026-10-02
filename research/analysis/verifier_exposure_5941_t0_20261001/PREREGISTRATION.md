# Issue #5941 T0 — finite peer-exposure provenance witness

## H / T / D / C / U

- **H:** A count-only quorum can admit a false PASS when a wrong first-pass verdict is copied by a peer-exposed verifier; removing peer-exposed or unverifiable receipts from the independent first-pass vote set should turn the planted 2-to-1 false PASS into `UNKNOWN_INDEPENDENCE`, without treating shared raw evidence as a peer-verdict edge.
- **T:** Enumerate all 8 triples of PASS/FAIL verdicts, crossed with four V2 exposure classes (`none`, `peer_verdict`, `raw_observation`, `unknown`) and valid/invalid content-bound commitment, plus omitted/forged-edge adversarial controls. The candidate emits per-row count-only and exposure-scoped outcomes. A separate auditor derives expected decisions directly from raw votes and checks complete ordered coverage.
- **D:** Method-scoped pass requires exactly 66 rows, matching independent outcome reconstruction, raw count-only PASS on the planted copied-verdict counterexample, no exposure credit for unknown/invalid receipts, and no corruption control can create scoped PASS from fewer than two valid unexposed receipts. Any mismatch is FAIL/HOLD.
- **C:** Dynamic exposure accounting is unnecessary if all receipts are independently captured at the call boundary; or #5314 static domain controls already prevent the constructed false quorum.
- **U:** The finite model assumes exposure and commitment metadata are truthfully captured. It does not test LLM conformity, falsifiable call-bound capture, GUI effects, costs, or deployed verifier policy.

## Frozen execution

Base main: `2b899413d30fcee0ce97e7c69d83f7b2f69e89dd` (observed 2026-10-01). Standard-library CPython on Windows host; CPU only. No Docker/GPU/model/GUI/network/input. Construction: `python -m unittest -v` (4 tests) and `python -m py_compile runner.py audit.py test_runner.py`. Candidate: one invocation `python runner.py`; independent raw-only auditor: one invocation `python audit.py raw-candidate.json`. No retries after candidate/audit start.
