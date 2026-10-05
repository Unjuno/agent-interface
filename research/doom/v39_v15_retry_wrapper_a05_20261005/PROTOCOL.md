# A05: retry-owner composition through the V15 release-batch wrapper

## H/T/D/C/U

- **H:** With the exact current-main release-batch backend v1 and transition-owner v4/v3 composed around PR #7974's input-owner v12, a deterministic dropped first key-up is recovered and the wrapper publishes a verified empty two-key batch. The retry's keymap samples will be audited for insertion between explicit UP injections, against A04's frozen no-inter-UP-query invariant.
- **T:** One FakeXlib execution of the real release-batch backend class. Its minimal typed-backend-v2 parent shim issues DOWN(a), DOWN(b), UP(b), UP(a); FakeXlib drops the first KeyRelease for keycode 31 only. The exact PR #7974 owner source is used. No real X server, game, model, GUI, or OS input.
- **D:** Preserve ordered raw trace, per-key release rows, owner receipts/attempts, post-batch state, final synthetic keys, and an independent auditor result. PASS only if recovery, identity-bound receipts, two-row verified empty release batch, and querymap interleaving are all observed. Any other result is retained as FAIL or STOP without retry.
- **C:** Candidate and audit sources from current main `6a2826d391b77496b69752609a6f07b6971b4b6f`; retry owner overlay from PR #7974 head `4d1cb80a5018cc4f392146eae880d98c33a84bde`; WSLc, pinned Python 3.11.9 linux/arm64 image `python@sha256:8fb099199b9f2d70342674bd9dbccd3ed03a258f26bbd1d556822c6dfc60c317`, network disabled, read-only root, one CPU, 512 MiB memory, 32 MiB tmpfs. Candidate and runner hashes checked before candidate start.
- **U:** Synthetic owner/wrapper composition and call-order evidence only. No V15 session startup, actual X11, physical/application state, V39 threat exposure, useful task feedback, latency, recovery under a real environment, or live allocation claim. A05 does not supersede A04's ordering contract; it tests the candidate's compatibility with it.

## One-shot decision gate

Run `runner.py` exactly once after the frozen hashes validate and the pinned image is confirmed locally available. If image or setup is unavailable before candidate start, record STOP and do not pull or retry. After candidate start, preserve the first raw output and audit output regardless of PASS/FAIL. PASS requires every named check in `audit.py`, including an explicit keymap query between the first and last UP injections; this establishes that retry recovery composes through the wrapper while violating the A04 ordering invariant. It is not a live-input result.
