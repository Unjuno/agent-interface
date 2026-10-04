# A05: exact invocation-count type guard for the A04 audit

## H / T / D / C / U

- **H:** The A04 raw-only auditor's `candidate_invocations == 1` check accepts JSON `true`; an A05 wrapper can require an exact integer and preserve acceptance of integer `1`.
- **T:** Re-audit the frozen A04 result and retained source only. Compare A04 behavior on the boolean mutation with A05 behavior; test integer, boolean, float, string, and null counts.
- **D:** PASS only if the unchanged A04 record audits under A05, exact integer `1` passes, and every non-exact-integer or non-one value fails.
- **C:** This is a narrow audit-contract repair. It does not rerun the A04 candidate or alter its historical bytes.
- **U:** Validates one claimed invocation-count field in a retained fake-display composition. It does not establish candidate execution count independently, runtime integration, live input, GUI/game effect, useful feedback, recovery, threat response, or MAP01 progress.

## Result

A04 accepts the mutation `candidate_invocations: true` because Python equality treats `True == 1`. The A05 gate rejects that value with an exact-type check while accepting exact integer `1`. The retained A04 `FREEZE.json`, `RESULT.json`, `AUDIT.json`, source files, and checksums are copied byte-for-byte under `SOURCE/A04/`; no candidate, fake display, OS input, game, or model ran.

Run `python3 build_freeze.py`, `python3 -m unittest -v test_a05.py`, `python3 -O -m unittest -v test_a05.py`, then `python3 audit_a05.py`.
