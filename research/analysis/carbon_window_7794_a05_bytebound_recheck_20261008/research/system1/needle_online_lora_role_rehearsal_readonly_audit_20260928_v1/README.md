# Issue #4895 read-only raw audit addendum

This is a post-hoc integrity and recorded-prediction audit of the immutable formal output for [Issue #4895](https://github.com/Unjuno/agent-interface/issues/4895). It does not replace or upgrade the registered `HOLD_AUDIT_INTEGRITY` disposition, and it does not rerun any formal seed.

## H / T / D / C / U

**H — audit question.** Can a standard-library-only audit independently verify the retained freeze/raw/invocation identities, recompute held-out accuracy metrics from all 144 saved prediction rows, and distinguish exact B_ONLY versus B_DUPLICATE_CONTROL record equality from equality of their recorded predictions?

**T — immutable inputs and one read-only audit.** Inputs were fetched from merged commit `086233b30090d56b117a648226367a529dd553ad`, under `research/system1/needle_online_lora_role_rehearsal_v1/`. `FREEZE.json` SHA-256 is `cffa4feaf36cdaeaf899e0f4ddadefb30ae2d0c59059a87dc76dd7b93c705d9b`; the frozen `audit.py` SHA-256 / Git blob are `02d9a98a6eee494ef8f04edee22b84224312dfc8cd33f26ba96039f197f49b32` / `697c6068cbfe878338f78347fd4fa1e7b7e9a651`. The compressed formal raw is Git blob `fa2c21de7f55fa9c5c50c06c01e450120106efce`, 361,312 bytes, SHA-256 `8754ceac5be2c46bb876ca0703a824337e395409caa8a69fef2eea72a1b00ab8`; its decompressed JSON is 964,795 bytes, SHA-256 `ed4560d01c99adb74230758c6c6bb22458159d1b76e790836c0936c3cac15349`.

The single local audit command was `python -B run_capture.py <retained-artifact-root> <empty-output-directory>`. `run_capture.py` refuses a non-empty output directory, then invokes the separate standard-library-only `audit_raw_stdlib.py`; exact argv, host/Python version, stdout/stderr bytes and hashes, output hash, and zero GPU/Docker/model/optimizer activity are retained in `out/RUN.json`. The audit verifies the recorded invocation image, CPU-only argv and bind destinations, as well as receipt/raw/stdout/stderr hashes and counters. A separate wrapper check of the non-empty-output guard passed with all four pre-existing output files byte-identical (`outdir_guard_test.json`). No input, frozen source, formal raw, or registered audit was modified. The auditor reads the saved predictions; it does not import `runner.py` or `audit.py`, load PyTorch, replay optimizer steps, or fit a model.

**D — decision.** `PASS_RAW_IDENTITY_AND_DESCRIPTIVE_RECOMPUTATION`: all checked hashes and invocation bindings match; the formal receipt records exit 0, one orchestration, zero retries; all 144 rows parse with expected seed/arm/arrival counts; all stored predictions recompute against the stored held-out labels; the 48 B_ONLY/B_DUPLICATE_CONTROL checkpoint pairs have identical recorded predictions. The full checkpoint JSON differs at 48/48 pairs; maximum absolute scalar deltas are `3.5762786865234375e-07` in adapter values and `1.7881393432617188e-07` in optimizer state. The sidecar's first digest token matches the freeze bytes, while its trailing `FREEZE.json` filename means comparing the entire sidecar line to the bare digest produces the registered `freeze_hash` error.

Recomputed final A/B accuracy for A_REHEARSAL was 0.1992/0.7930, 0.5898/0.4883, and 0.9727/0.0273 across the three seeds. None passes the frozen per-seed quality gate. These are raw-derived descriptive values only; the registered HOLD remains in force, and this addendum does not relabel it as a scientific FAIL or PASS. The observed tensor/state deltas are consistent with why exact JSON equality rejects the duplicate-control trajectories, but this read-only audit does not establish their cause or prove optimizer-trajectory equivalence.

**C — controls.** The audit verifies SHA-256, the compressed raw's Git blob identity, freeze/source identity, sidecar digest token, formal receipt/raw/stdout/stderr bindings, inspected image and CPU-only invocation argv/mounts, exact ordered seed denominator, allocation/arms, per-seed held-out row counts and within-split uniqueness, base immutability receipts, update counts/duration bounds, all 144 saved prediction arrays against their recorded labels, and the exact registered error list. All checks are standard-library operations on retained bytes. It does not modify predecessor artifacts.

**U — limits.** One retained synthetic CPU allocation and one host-side raw-only pass. No optimizer replay, GPU work, new training, new task, independent model-quality inference, correction of the frozen auditor, causal explanation of floating-point differences, or change to #4895's formal disposition is claimed. The original `FORMAL_REPORT.md` and registered audit remain authoritative for the allocation's `HOLD_AUDIT_INTEGRITY` status.

## Reproduction

Place `audit_raw_stdlib.py`, `run_capture.py`, and `test_output_guard.py` together. Supply the original retained artifact directory containing `FREEZE.json`, `FREEZE.sha256`, `audit.py`, `formal/FORMAL_INVOCATION.json`, `formal/formal_result.json.gz`, `formal/docker.stdout.bin`, `formal/docker.stderr.bin`, and `formal/audit/AUDIT.json`. Run the auditor with a new empty output directory, then use a separate already-nonempty directory for the guard check:

```powershell
python -B run_capture.py <retained-artifact-root> <output-directory>
python -B test_output_guard.py <retained-artifact-root> <nonempty-output-directory> <guard-receipt.json>
```

Both scripts use only Python's standard library. `SHA256SUMS.txt` binds the published files in this addendum; the original input identities are recorded above and again in `out/READONLY_AUDIT.json`.
