# Construction record — Issue #6367 T0

Allocation: `EXPOSED-SUCCESS-AUDIT-6367-T0-20261002-01`

Base: `c6e4c7ad413bcc9605ab5bf00df0eaa4ac7ba560`
Formal candidate/audit invocations at this record's freeze: **0 / 0**.

## Test-first history

- Initial candidate tests were written before `candidate.py`; `python3 -B -m unittest discover -s tests -p 'test_candidate.py' -v` failed with the expected `ModuleNotFoundError: No module named 'candidate'`.
- The first candidate implementation exposed an over-specific test expectation: actual arm summaries correctly contained failure/unknown/safety counts in addition to denominator and success rate. The assertion was corrected to the hand-derived complete summary; no candidate behavior was changed for that assertion.
- Auditor tests were written before `auditor.py`; the expected `ModuleNotFoundError: No module named 'auditor'` was observed.
- A new malformed-input test then caught Python's `bool`-is-an-`int` subtype behavior: `down_ms=True` was incorrectly admitted as a timestamp. The candidate was tightened to require exact integer types; the independent auditor already uses the same strict type boundary.

## Construction gates (not the formal allocation)

On Ubuntu 24.04.4, Python 3.12.3, WSL2 kernel `6.18.40.1-microsoft-standard-WSL2`:

- `python3 -B -m unittest discover -s tests -v` — **12/12 PASS**.
- `python3 -B -O -m unittest discover -s tests -v` — **12/12 PASS**.
- `python3 -B -m py_compile candidate.py auditor.py tests/test_candidate.py tests/test_auditor.py` — **PASS** (the command completed before the following combined one-liner hit a shell-quoting error).
- The first combined AST/JSON check command had nested-quote damage and exited before its check expression ran. It was replaced with `python3 -m json.tool` for each frozen fixture; both parsed successfully (`JSON_PARSE_PASS`). This was a command-construction error, not a fixture or candidate result.
- `python3 -B research/check_workspace_index.py` at repository root — **154 top-level directories reachable**.
- `python3 -B .github/check_public_navigation.py` — **26 documents / 1,235 repository-relative links PASS**.
- A final repeat used a misspelled worktree path (`...exposed_success_audit_6367_t0-20261002`, hyphens instead of underscores) and exited before launching either test suite. The corrected commands above ran both suites successfully at 12/12. This is a launcher path typo, not a test or candidate outcome.

The one candidate invocation and one raw-only independent audit have not run yet. No formal outcome is inferred from these construction checks.
