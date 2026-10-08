# Current-context admission repair — #6877 / #57

At main `f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549`, core admission compared
caller-supplied current time and freshness identifiers without validating their
scalar domains. A negative time could admit; booleans/floats compared equal to
integer observation and binding identities; some malformed clocks escaped as
TypeError. The repair applies the existing strict bounded-integer helper to the
three current-context arguments within the established ContractError refusal
boundary. Refusal remains INVALID_PROGRAM with empty required capabilities.

Worker `01a0ff2d-be6f-78d3-ad7c-497514c9079f`, policy FINAL-v5. Ownership is the
three lines in `admit_program`, the new regression file and this additive package.
The separate manifest enum repair #6854 is not incorporated or rewritten here;
#6853's committed lifecycle content/proposal also remains unchanged. These are
ordinary engineering checks against #57's guarded admission requirement, with no
formal allocation, backend, user input, model, container, GPU or shared lease.

## Executed result

Native Windows, CPython 3.12.10, sequential standard-library execution.

- Initial exact-main 19-row discovery: seven malformed contexts admitted and
  three malformed clocks escaped as TypeError. Its raw is preserved separately.
- Before new regression repair: three methods, 26 subtest assertion failures and
  four TypeError errors, exit 1. Existing 65 core methods passed before the change.
- After repair: all 68 core methods pass, exit 0; core compilation passes.
- The fixed 44-input corpus is recorded once per before/fixed source. The corpus
  includes bool, float, string, null, containers, negative and oversized integers,
  valid zero/current/max integers, and exact/after-expiry controls.
- The independently implemented raw-only oracle reconciles all 44 rows at both
  stages. Baseline has 30 decisions differing from the strict-context rule and
  four unexpected exceptions; repaired source has zero mismatches/exceptions.
- All nine copied-output corruptions are rejected, including JSON integer/bool
  substitutions in context and result. Identity comparison uses canonical JSON,
  preserving the distinction that Python dictionary equality erases.
- The applicable CLI workflow ran 121 methods: 115 pass, six platform skips,
  exit 0. Core doctor, CLI doctor and workflow compilation exit 0. Host discovery
  does not grant input authority; the skipped foreign-platform tests are unverified.

`PASS_CONTEXT_REFUSAL_SCOPED` is a caller-boundary result. The separate auditor is
by this same author, so external non-author review is still required. UTC matrix
start/end, interpreter version, fixture/source hashes and raw hashes are retained.
The source hashes are exact executed bytes and must match the staged Git blobs;
there is no inferred newline conversion or source identity substitution.

## H / T / D / C / U

H: malformed current scalars refuse before time comparison and freshness matching.
T: test-first reproduction, frozen 44-input before/fixed matrix, raw-only reference
and nine corruption controls, plus appropriate core/CLI workflow checks.
D: invalid contexts return the existing typed refusal without an unexpected Python
exception, while valid/current/stale/expired controls preserve prior decisions.
C: Python type hints and coercive numeric equality do not enforce runtime identity;
the existing integer helper suffices without a broad exception catcher.
U: this checks decoded caller data only. It does not establish observation
currentness, clock-domain synchronization, native authority, release timing,
physical execution, thread safety, model/task benefit or performance. The existing
inclusive expiry equality (`now_ns == expires_at_ns`) is explicitly preserved,
not endorsed as a newly validated policy.

The common fleet deadline was not established or reset. No shared resource lock
was acquired. Main application requires a fixed content proposal/committee,
two eligible non-author approvals, current-main combination verification and
conditional application under actual GitHub requirements.

## Reproduction

Select fresh output paths; retained raw/audit files are never overwritten:

```sh
python -m unittest discover -s runtime/core_v1 -p 'test_*.py' -v
python -m compileall -q runtime/core_v1
python runtime/results/admission-context-01a0ff2d/run_matrix.py before /fresh/before.json
python runtime/results/admission-context-01a0ff2d/run_matrix.py fixed /fresh/fixed.json
python runtime/results/admission-context-01a0ff2d/audit.py /fresh/audit.json
```

The matrix before mode reads the pinned Git source, not an old experiment. Fixed
mode reads current source and reports its exact hash. The auditor reads retained
raw, frozen fixtures and source identity without importing runtime code. A source
change correctly invalidates the retained fixed-source gate. Retained log originals
stay private; public copies remove private workspace/home prefixes. The publication
manifest binds public bytes; workflow receipts identify original executed logs.
