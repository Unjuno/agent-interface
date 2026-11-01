# WSLc held-input display replacement trials

Raw conditions, fixture source, receipts, target events, stderr, exit status and amendments are retained byte-for-byte in each ZIP. SHA-256 values and file counts are in MANIFEST.json; every archive member was compared to its source before commit.

- r428: FAIL; repeat events made the preregistered release-event gate fail.
- r429: ERROR, then outer timeout 124; xset was absent. Planned r430 was not run.
- r432: one repeat-off no-cancel control, scoped PASS.
- r433: one repeat-off cancel trial, scoped PASS; old cleanup UNKNOWN and release unconfirmed.

Each is one private synthetic WSLc trial. Repeat-off results are consistent with, but do not prove, an auto-repeat explanation for r428. No automatic recovery, old-input release, whole-task completion, or general reliability claim. The separate amendment in r428 and r433 corrects the interpretation of cancellation input_dispatched=false: it describes the cancellation signal, not the earlier input.
