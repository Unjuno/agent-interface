# Issue #4998 — two-phase skill-card boundary

Successor to #4976's retained construction stop. This allocation preserves #4976/#759 and tests only an additive caller-visible boundary; it is not the separate model-facing three-arm study.

## H / T / D / C / U

- **H:** Across the eight frozen cases, candidate presentation and explicit selection are separate; no detail is loaded before selection. A HINT remains `REVALIDATION_REQUIRED` until a separately recorded current revalidation yields a session/case/version/provenance-bound `ADMISSION_DEPENDENCY` receipt. All invalid transitions fail before detail load.
- **T:** Run `formal_entry.py` exactly once in local Docker using the pinned image ID below, no network, read-only root and source, and a fresh writable output directory. The entrypoint runs the frozen case runner, a standard-library raw-only independent auditor, and eight copied-evidence mutations.
- **D:** PASS only if all eight rows, event orders, scoped receipt, registry immutability, seven refusal controls, zero effects, and all eight mutation rejections reconcile. Any missing source, live Docker owner, non-empty output, image mismatch, or failed preflight is a pre-invocation STOP; never retry the formal allocation.
- **C:** Exact #759 `model.py` and `cases.json` source snapshots; zero model/GUI/action/authority. This is a synthetic loader-boundary proxy, not skill execution.
- **U:** One eight-case synthetic construction on one Windows/Docker Desktop host and one image. No model/tokenizer/LLM, latency, quality, actual application effect, real caller, or product/runtime claim.

## Frozen identity

- Issue: [#4998](https://github.com/Unjuno/agent-interface/issues/4998)
- Allocation: `skill-card-two-phase-4976-20260928-02`
- Source branch: `research/skill-card-two-phase-4976-20260928-02`
- Base main: `4fa988e2872e20f4da840c91fbdd83a8d0ff8d12`
- Original #759 source blobs: `model.py` `8f07d25daa8cfc8df175fe9c42bf5345d0875b9d`; `cases.json` `75ee2a59672b090b7980b8c20be6d41f72c6a21d`
- Image: `python:3.12-slim-bookworm`, `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, linux/amd64
- Docker limits: `--pull=never --network none --read-only --cap-drop ALL --security-opt no-new-privileges --cpus 0.25 --memory 256m --pids-limit 32`; `/tmp` is bounded tmpfs; `/src` is read-only; only the fresh `/out` bind is writable.

## Local execution

From repository checkout with a verified empty, allocation-specific output directory:

```powershell
$src = (Resolve-Path .\research\coordination\skill_card_two_phase_4976_v2).Path
$out = (Resolve-Path .\outputs\skill-card-two-phase-4976-20260928-02).Path
docker run --rm --pull=never --network none --read-only --cap-drop ALL --security-opt no-new-privileges --cpus 0.25 --memory 256m --pids-limit 32 --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount "type=bind,src=$src,dst=/src,readonly" --mount "type=bind,src=$out,dst=/out" python:3.12-slim-bookworm python -B /src/formal_entry.py
```

The formal run may start only after the concurrent Issue #4990 Docker allocation has explicitly released the shared local engine. Record invocation output and all files under `out/`; no hosted workflow is part of the experiment. If that release is not available, record a typed STOP and do not launch.
