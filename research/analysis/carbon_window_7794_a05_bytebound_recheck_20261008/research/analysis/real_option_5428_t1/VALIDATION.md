# T1 validation record

- Preregistration was posted before the factorial candidate invocation: Issue #5428 comment `5911326638`.
- Host `python3 -m py_compile` on the frozen candidate, auditor, smoke test, and corruption controls: PASS.
- Host and network-disabled `python:3.12-slim` smoke: PASS; only a single hand-authored construction case was invoked.
- Formal container candidate: exactly one invocation after preregistration; exit 0; 2,304 scenarios retained in `raw/formal.json`.
- Independent network-disabled container audit: auditor PASS; preregistered model gate FAIL; runtime transfer UNCERTAIN.
- Four corruption controls: 4/4 rejected.
- No model/GUI/runtime claim, candidate mutation, formal retry, or threshold adjustment.
- `python3 research/analysis/check_index.py --write` and subsequent read-only index check: PASS, 214 result/failure directories indexed.
- `python3 research/check_workspace_index.py`: PASS, 146 top-level research directories reachable.
- `python3 .github/check_public_navigation.py`: first local invocation stopped because the newly created directory was not yet tracked; after staging only this evidence path and generated analysis index, rerun PASS (26 documents, 923 relative links).
- `git diff --check`: PASS after staging.
