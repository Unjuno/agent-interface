# Research Preview retained source audit R01

Status: PASS_FROZEN_SOURCE_AUDIT; offline integration check only.

- Base main: `128c33f22a042b83a51351debdc32ef3ae5bfa4b`; final candidate implementation commit: `6c50fdce0d857fbf1a7c647bcd6ca9a17f8c05c0`.
- Frozen experiment source commit: `54910c6f9f0594c609f1f3c6895a918caa64130f`; archived source files verified: 29; archive mismatches: 0.
- Current source content drift, compared with the archive after line-ending normalization: 7 of 29 files. This matches Git-blob comparison; checkout conversion is not counted as content drift.
- Retained outcome remains `RETAIN`, six tasks per arm, break-even task 2.
- Local tests: retained-audit tests 5/5 normal and `-O`; preview bundle builder 6/6 normal and `-O`; actual retained audit exit 0.
- The supported Ubuntu WSL builder passed on the final candidate: 22,646 selected files, 30 frozen-source archive members, exact selected closure, launcher modes preserved, checkout/archive launcher preflights passed. Extracted artifact audit passed with 29/29 frozen sources and seven later content differences. Artifact size 349,878,418 bytes; SHA-256 `73147dc192c7b472a47a4730b7886fe297beb75182cad2f677b368232ae38ef8`. Raw receipts and artifact locator are in [supplemental R06](supplemental-linux-build-r06-20261122/RESULT.md).
- Windows is not a supported package-build host for this launcher; its expected POSIX preflight STOP is retained separately. An earlier incomplete WSL object-fetch attempt is separately marked not adjudicable in [R04](supplemental-linux-fetch-abort-r04-20261122/RESULT.md).
- No live mode, model call, GUI, allocation, task action, dependency installation, or publication occurred. The package build verifies artifact construction/startup boundaries only; it does not satisfy the frozen RC1 supported-host doctor, fresh no-retry golden run, or `audit-live` acceptance.
