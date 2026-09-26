# Frozen H/T/D/C/U — Docker Desktop host validation

## H / Hypothesis

The exact final Issue #3683 five-test suite and raw-only CLI pass in two fresh network-disabled Linux/amd64 containers under Docker Desktop 28.5.1, with the second output byte-identical to the retained baseline.

## T / Test

- Allocation: `issue-3690-dockerdesktop-host-01`.
- Source commit: `de9acd02b50fac4e9b8c46ed961d923181cbbece`.
- Exact sources are retained unchanged in main at `research/issue_3676_audit_hardening_v1/` and each Git blob ID/SHA-256 is pinned in `SOURCE_MANIFEST.json`.
- Container 1, once: `python -B -m unittest -v test_audit.py`; expect 5 tests.
- Container 2, only after container 1 exits zero, once: `python -B audit.py evidence/raw.json --freeze evidence/predecessor_FREEZE.json --study-freeze evidence/FREEZE.json --output /out/hardening_audit.json`.
- Independently validate CLI return code, status `PASS_OFFLINE_STRUCTURAL_AUDIT`, zero errors, 21/21 corruption controls rejected, exact bytes equal the retained `evidence/hardening_audit.json`, and SHA-256 `e2ac7b32c1da563cbcd3cbea285ac5ace4f98d43b3cb9ea046d2bf6c1adbbbc0`.

## D / Decision

`PASS_DOCKERDESKTOP_HOST_VALIDATION_SCOPED` iff Docker Desktop is exactly 28.5.1 Linux/x86_64, the cached immutable image is the pinned linux/amd64 image, all source hashes/blob IDs match, five tests pass, the second container exits zero, its raw-only output is byte-identical to the retained audit, and all 21 negative controls are rejected.

Any preflight/provenance mismatch is `STOP_*` before formal container work. Any first-container nonzero stops before the second. Any CLI/audit mismatch is `FAIL_*`. Preserve partial logs/results; never repeat either formal container invocation.

## C / Constraints

Docker context `desktop-linux`; server 28.5.1; image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `--pull=never --platform linux/amd64 --network none --read-only`, exact source directory read-only, dedicated fresh evidence output, 64 MiB tmpfs, 1 CPU, 512 MiB, 64 PIDs, all capabilities dropped, no-new-privileges. No source mutation, XRes/X11 allocation, input, game, model, workflow, network, or Docker cleanup.

## U / Limits

This checks one exact source snapshot and Docker Desktop engine path only. It does not prove arbitrary auditor soundness or XRes guard correctness. The prior OrbStack evidence is complementary, not replaced or pooled.
