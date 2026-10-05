# A12 — preserve a completed two-key release prefix on the latest PR head

**H:** If owner cleanup confirms an earlier key-up and a later held-key release sync fails, the candidate may discard the earlier per-key measurement before appending its aggregate `owner_release` record.

**T:** On exact current PR head `84985b2b878f99551ab924fbc1351139915f5cc0`, admit F8 and F9 in the fake-display harness, inject a failure at the second release sync, drain owner records, and then attempt another DOWN under that lease. Run RED with the unmodified owner source at the pinned PR head and GREEN with the candidate fix.

**D:** PASS requires RED to show zero drainable release measurements; GREEN must preserve exactly the F8 `CONFIRMED_PHYSICAL_UP` in a single `verified=false` partial owner-release record without aggregate fields, fault the owner, and reject follow-up DOWN before injection.

**C:** Deterministic fake-display fault path; no frequency estimate or real X11 claim. This A12 owner-loop repair is separate from the current PR A11 bridge emitter ambiguity stop. Both regressions run together in the 16-test suite.

**U:** Windows 10 build 26300, CPython 3.11.9; fake display only. No real X11, OS input, application effect, live allocation, gameplay, safety, recovery efficacy, or latency evidence.

Baseline source and candidate/dependency hashes are in `A12_SOURCE_LOCK.json`. RED/GREEN outputs are in `owner-ledger-a12-red.log` and `owner-ledger-a12-green.log`; suite outputs are in `candidate-suite-a12*.log`, `executor-v12-expiry-a12.log`, `owner-compat-a12.log`, and `existing-bridge-a12.log`.
