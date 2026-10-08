# COMMIT-BUSY saved compatibility evidence rescue

Source PR #7044, exact original `c4cb04b99a138a47c230f240d93e7d994beee597`.
All 20 original packet files restored unchanged on main base
`abb6f6f9c71f7c61db77070f0ced3c4bc2439dcd`.

Rescue validation invokes only the reviewed saved auditor's pure `check(rows)`
function, not its guarded main, producer, endpoint subprocesses or launcher.
Manifest byte lengths/SHA-256 and six decoded DB capsule identities are checked.
This is preservation and saved-row consistency, not a new SQLite execution,
fresh DB content reconstruction, Windows compatibility or independent review.

First harness attempt failed before checking rows: `NameError: __file__ is not
defined` at saved-audit line 3. The adapter then supplied the original file path;
no source/data or decision changed and no original experiment was repeated.

Original COMMIT-only versus repeated-UPDATE result remains limited to known
reader-caused SQLITE_BUSY with an active transaction. Lost responses, arbitrary
errors, real task effects, GUI/model and parent #6526 H_PASS remain unproved.
Original FINAL-v5 adoption gate is unchanged; no approvals are invented.
Saved checks exited 0: 19 manifest targets, zero mismatches; six rows and six
decoded capsule hashes agree. Local workflow replay at `dd8eaabd31` exited 0:
43 steps, failures=[]; full output is `local-ci.log`. This is not hosted CI,
full runtime or native compatibility certification. Main integration remains
pending. Source retirement is not yet safe.

Fresh PR review readback found the prospective threshold-two committee
descriptor, but no acceptances/approvals:
https://github.com/Unjuno/agent-interface/pull/7044#issuecomment-5969081888
The outside-committee supplement is explicitly zero votes and cautions against
generalizing BUSY recovery to SQLITE_INTERRUPT or broad error-family membership:
https://github.com/Unjuno/agent-interface/pull/7044#issuecomment-5969229938
These links preserve interpretation and publication failure qualifications;
neither a committee nomination nor this rescue supplies an application certificate.
