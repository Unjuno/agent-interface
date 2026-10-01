# Issue #4678 — GPU invocation guard preflight

## H/T/D/C/U

- **H:** An allocation-scoped atomic claim, exact command/image/input digests, and an fsynced terminal record can permit one zero-step GPU construction smoke and refuse same-process and restarted-process duplicate launches before Docker.
- **T:** One local allocation with `cactus-needle3-train:4205-v1`, then two refusal controls. No fit, optimizer, package install, network, or model download. The frozen checkpoint must match the #4205 `TRAINING_FREEZE.json` identity exactly.
- **D:** `PASS_SINGLE_INVOCATION_GUARD_SCOPED` only after one recorded zero-step invocation, both refusals before container launch, unchanged first receipt, and independent ledger audit. `FAIL_DUPLICATE_INVOCATION_ADMITTED` if a duplicate reaches Docker. `STOP_LOCAL_IMAGE_OR_GPU_UNAVAILABLE` if exact runtime/checkpoint identity cannot be verified. `HOLD_DURABILITY_OR_AUDIT` if receipt durability or audit cannot be established.
- **C:** Local Windows 11 / Docker Desktop, cached #4205 training image and checkpoint only; one host and one allocation. GPU identity/availability is observed, not a GPU-vs-CPU treatment.
- **U:** No model quality, fit, speed, multi-host race, crash/power-loss, GitHub immutability, or production orchestration claim.

## First outcome

**`STOP_LOCAL_IMAGE_OR_GPU_UNAVAILABLE` before invocation.** The cached #4205 training image was present and its exact image ID matched the frozen pin. RTX 3080 identity and free VRAM were present. The exact 242,047,978-byte `needle3.safetensors` checkpoint (`c234c70d…`) was not present in the local Hugging Face snapshot or the cached #4205 training image inputs. The only cached Cactus file was the distinct 35,335,380-byte `needle3.cact` with SHA-256 `c9d915ec…`, which belongs to the separate #4204 base artifact and cannot substitute for the frozen checkpoint. No #4205 training-image container was launched, no checkpoint was loaded, no optimizer step occurred, and no network/download was attempted. Two separate offline CPU-only containers ran only the independent stop-record auditor and mutation tests.

This is a preflight STOP for #4678, not a guard PASS/FAIL and not a model-quality result. The guard invocation allocation was not consumed because the wrapper/smoke command was never started. Preserve this STOP; any future run after a resource change requires a separately frozen successor allocation.

The independent read-only audit container used local image `python:3.12-slim-bookworm` (`sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, linux/amd64, network none). It passed 5/5 mutation tests and the raw-only STOP audit with zero errors.

See `PREFLIGHT.json`, `COMMANDS.md`, `AUDIT.json`, and `VERIFICATION.json` for identities, observations, and checks.

