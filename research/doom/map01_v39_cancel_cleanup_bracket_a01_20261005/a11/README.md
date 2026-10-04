# A11 cleanup-record integrity audit

## H/T/D/C/U

- **H:** The A10 validator can accept duplicate admission or per-key release
  rows because it first projects them into dictionaries, and it does not bind
  the reported confirmed-up classification to `release_attempted=true`.
  Actuation IDs must also remain unique across distinct admitted keys.
- **T:** Keep A03's candidate bytes immutable. Re-run a separately frozen,
  read-only audit and in-memory mutation controls under the pinned Python
  container. Mutate duplicate admission/release rows, false/missing
  release-attempt flags, and cross-key actuation-ID reuse.
- **D:** PASS only if the unmodified retained raw passes and each corruption
  returns at least one audit error; fail the audit if any source hash or Python
  version differs from the freeze.
- **C:** A10 raw source audit is not rewritten. A11 checks row cardinalities
  before mapping, one-to-one per-key admission/release matching, globally
  unique actuation IDs, and explicit release-attempt status.
- **U:** This is offline integrity evidence over an old fake-display trace. It
  does not establish OS-level input, exact physical edge time, app consumption,
  useful feedback, threat response, recovery, safety, or MAP01 completion.

## Finding and outcome

The tested A10 validator returned an empty error list after (1) duplicating
an admission row, (2) duplicating a cleanup release measurement, (3) setting
`release_attempted=false`, and (4) removing `release_attempted`. A11 rejects
these mutations and cross-key actuation-ID reuse. The original A03 raw SHA-256
is `36b60282cfc2a7c328cdb7c62ec0d37b029808dc7cf2f6e327d0fd954fd3c99d`;
the candidate was not rerun.

## Reproduction

Using the pinned image in FREEZE-A11.json, from this directory:

```sh
python audit_a11.py
python -m unittest -v test_a11.py
python -O -m unittest -v test_a11.py
```
