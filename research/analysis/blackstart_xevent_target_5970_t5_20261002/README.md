# Issue #5970 T5 — X event target diagnostic

This no-input successor investigates the T4 source-bound Tk event delivery gap by querying the app window tree and core event masks. The exclusive-mask expectation was falsified on the tested root; the prior T4 event-window ID was not present in the T5 tree. H/T/D/C/U and one-shot gates are in `PLAN.md` and `FREEZE.json`; evidence and scope are in `RUN.md` and `REPORT.md`; exact hashes are in `SHA256SUMS.txt`.
