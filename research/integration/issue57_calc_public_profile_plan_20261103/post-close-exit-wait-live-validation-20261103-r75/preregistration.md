# Preregistration: post-close exact Calc exit observation r75-c1

Date: 2026-11-03. Single fresh validation attempt after the local two-phase close change. It is not a rerun or replacement for r73/r74 and is not an efficiency comparison.

## Question and frozen path

Does the public Calc lifecycle now close the guarded input owner before waiting for exact target exit, and can one fresh fixed-task attempt reach `interface_verify_task(status=verified, task_success=true)` with a naturally exited exact Calc generation? The fixed registered task is A1=731, A2=864. Use public prepare → launch → explicit review → compiled entry/save → independent pre-close file parse → guarded Ctrl+Q and 500 ms observation → public close → parent verification. One fresh Calc generation and one attempt only.

## Pass gates

Pass requires all of: (1) independent pre-close FODS values A1=731/A2=864; (2) both compiled transitions complete with `release_verified=true`; (3) close reports owner close verified, release readback confirmed, and no keys/buttons down; (4) exact target and oosplash exit receipt is verified with exit code 0 and `process_group_cleanup.clean_exit_verified=true` or `status=not_needed`; (5) parent verifier returns `verified` and `task_success=true`; (6) container exits 0. The new close-order behavior is recorded in the close lifecycle output; its source hash is frozen below. Any failure or unknown fails the single attempt. No retry, replacement, or post-hoc exclusion. If Ctrl+Q does not close Calc, allow the configured parent custody cleanup; preserve task effect UNKNOWN if clean exit is not proven.

## Environment and controls

Pinned cached image `agent-interface-xvfb-mcp:late-input-r19`, image ID `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`; pull disabled. Docker Desktop 29.8.1, 8 CPUs, 24 GiB host memory, local log driver, existing WSL2 cap 24 GiB / 8 CPU / 8 GiB swap / gradual reclaim. Fresh container: 2 CPU, 4 GiB memory and swap, 256 PIDs, local logs, source read-only, evidence packet writable, no published ports. Debian 12, LibreOffice 4:7.4.7-1+deb12u14, Tesseract 5.3.0-2, Xvfb 1280x800. The control is the frozen full-OCR profile (`OCR_GUARD_CONTROL=always`); there is no A/B comparison. No provider/model/API call.

## Interpretation boundary

A PASS validates this one live close-order integration point only. It does not establish matched efficiency, WSLc, MAP01, broad reliability, or project completion. Docker settings are unchanged. Preserve every raw response and hash manifest.
