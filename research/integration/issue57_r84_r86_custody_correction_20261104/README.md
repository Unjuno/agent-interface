# Issue 57 r84–r86 custody correction — 2026-11-04

This is an additive byte-custody correction for the r84-c8, r85-c9, and r86-c10 startup-failure attempts. It does not change the original experiments or turn any startup failure into a live-control result.

The original `FREEZE.sha256` and its `.sha256` sidecar remain authoritative. Seven files that were only line-ending-converted were reconstructed from the tracked bytes and now hash exactly as frozen: r84 has 5/6 source files exact, r85 has 2/6, and r86 has 2/6. The freeze manifest itself is also verified against its sidecar in each run. The remaining 1/4/4 files respectively still mismatch their frozen SHA256 values. Searches of available Git history and the known local worktrees found no exact byte copies for those mismatches; this report preserves their observed hashes and does not infer original bytes.

Each attempt directory has three retained output files. No per-attempt manifest exists, so those files are listed with their current hashes and `retained_without_per_attempt_manifest`; this is not complete raw provenance.

Run `python verify_custody_manifest.py` from any directory to verify the current file bytes against this correction manifest. The verifier checks listed bytes and status accounting; it does not certify the correctness of the historical experiments.

The attempts remain setup failures with no demonstrated task effect, environment response, or input-release result. Their evidence cannot satisfy Issue 57's live comparison requirement.
