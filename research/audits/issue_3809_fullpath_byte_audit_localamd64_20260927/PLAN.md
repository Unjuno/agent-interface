# Issue #4649 — local amd64 byte-binding audit

Allocation: `issue3809-fullpath-byte-audit-localamd64-20260927`.

## H/T/D/C/U

- **H:** The preserved #4627 STOP is a basename/full-path lookup mismatch. The ten immutable main inputs will reconcile when the two audit-freeze roles are resolved by full repository paths; the untouched 246-byte accepted document and 23-byte delivered prefix will reconstruct exactly, and both frozen corruptions will be rejected by their byte receipts.
- **T:** Before the only formal invocation, pin main `522ff97664c12399e94e28462688afc905732373`, manifest blob `d5127266279299ada9ecb30af14a942370a3cc21`, the ten input SHA-256 values, local image ID/platform, this plan and all source hashes. Run a separate identity-only preflight. Then run one Docker formal invocation that checks input lineage/roles, untouched baseline, same-length accepted-content mutation, and delivered-prefix 23→22 truncation. A separate Docker invocation independently re-derives the result and runs copied-result corruption controls.
- **D:** PASS only if all ten paths and SHA-256 values match; audit freeze Plan/auditor hashes bind under their full repository-relative paths; historical formal freeze/raw remain explicitly ARM64 and internally agree; predecessor result dispositions remain unchanged; baseline has zero errors; same-length valid JSON is rejected by its producer hash; the 22-byte prefix is rejected by both receipt length and hash and remains invalid JSON; independent audit errors are empty; every corruption control emits structured FAIL with nonempty errors and empty stderr. Source/provenance mismatch before semantic parsing is STOP. Baseline or mutation miss is FAIL. Auditor crash or ineffective corruption control is FAIL_AUDITOR_ROBUSTNESS.
- **C:** Use only the already-cached image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, Linux/amd64, CPython 3.12.14. Docker `--pull=never --network none --cpus=1 --memory=1g --pids-limit=64 --read-only`, source/input read-only, distinct initially-empty output. No predecessor runner/auditor execution, network, install, model, GUI, OS input, workflow/Actions, or retry. This does not reproduce the former ARM64 run.
- **U:** Finite read-only audit of synthetic retained bytes on one local x86_64/Python build; no ARM64, CLI, OS/network truncation, production reliability, or product claim.

## Frozen input roles

Read the ten input entries directly from the manifest at the pinned intake commit. Preserve the original full repository-relative paths and expected hashes; the delivered-prefix bytes are transported locally as base64 text and decoded in memory before their SHA-256 is checked. Never parse baseline semantics unless all source, manifest, path, hash, freeze-role, and lineage checks pass.

The formal runner and independent auditor are separate programs. The auditor must not import the runner or predecessor audit source. The formal invocation is exactly one; preflight and mutation controls are excluded identity/integrity checks and cannot generate or replace formal rows.
