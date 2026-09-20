# Issue #3655 — committed-bundle audit result

**Data integrity:** `HOLD_COMMITTED_ARTIFACTS_INCOMPLETE`  
**Container execution:** `STOP_CONTAINER_UNAVAILABLE`  
**Formal allocation rerun:** no

The audited source is the exact Git tree at main commit `6b3c5fd93671c87fa02065da64afb397e7cdf62c`. The audit read Git blobs directly, so Windows `autocrlf` did not affect the source bytes. It enumerated the 15-file #3642 experiment tree, then materialized the nine committed files under its `evidence/` subtree into a temporary directory and ran the exact committed `audit.py` blob.

Results:

- `SHA256SUMS` lists 10 files. Eight exist and match their expected SHA-256 values exactly; zero present-file hash mismatches.
- `evidence/fixture.log` is absent; expected SHA-256 `536a06ebf82d1534ab63efb7e9216e6374980480bf74f677703afbb6a7f9e678`.
- `evidence/xvfb.log` is absent; expected SHA-256 `b987a262609a3720f450ab6815ed90b2069dd47b7b012959ca19c325aebf5d55`.
- The committed auditor exits 1 and returns `HOLD_OR_FAIL` with exactly `fixture.log retained hash` and `xvfb.log retained hash`. Its six raw-frame digests reproduce the committed audit record; all remaining checks pass.
- Exact committed auditor SHA-256: `eab5a025116904937a0e660014282a7e7222c0e6885bd783130d274f583f7f90`.

Docker Desktop was not usable during this turn: `com.docker.service` remained Stopped and the Windows Docker contexts did not report an accessible engine. The data-integrity result is still established locally from canonical Git objects, but no container claim is made. Formal GUI allocation #3642, its historical PASS, and its files were not changed. The original two log byte streams have not been recovered; no replacements were fabricated.

The full machine-readable result is `evidence/audit_result.json`. Reproduce with the command in `README.md` from any checkout containing the frozen commit.
