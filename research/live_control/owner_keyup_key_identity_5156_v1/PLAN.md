# Nullable-key identity audit successor (#5486)

This host-only experiment addresses the open fail-open mutation on PR #5467 without modifying that PR, its raw artifacts, or predecessor #5415.

## H/T/D/C/U

- **H:** Including nullable logical key in release identity causes the candidate audit to accept the pristine three-row artifact and reject explicit-key tampering, cleanup-null tampering, missing-key, and missing-row mutations.
- **T:** One frozen invocation of run_key_identity.py with candidate auditor SHA `79f95eadb29bc6cc35036c6ff424cb284e55849ecd76ccd2a841ae186a18d1cf`, exact PR #5467 legacy auditor SHA `191fdabdd289e49b03514d1dfc66ba475b885ab078b733a7ef7030daf9cfe906`, expected inventory SHA `9ef72a837ce4f5d802dcc7fdb72a843a0e768154dbe30897a00f270cfaabde2b`, and raw SHA `56842934b9f9b13fe0e52d515d31bd0c3d598cdb1cfa8b719dfb4c8ba463cbc2`. A separate raw-only audit checks the decision object. No source or fixture modifications after freeze.
- **D:** Require zero candidate errors on pristine input; exact identity-mismatch errors for both tampered keys; fail-closed missing-key and missing-row outcomes; show the prior auditor accepts both key mutations; independent audit must pass.
- **C:** Host CPython 3.11 standard library only; execute frozen GitHub sources in memory because local C: has zero free bytes. No Docker/X11/MAP01/model/GPU/network. #5085 has no transferred shared container lease.
- **U:** Synthetic integrity evidence only. It does not establish X11 release intervals, physical key-up, live MAP01 held-input occupancy, useful feedback, or bounded recovery coverage.
