# Issue #5013 — one-case ARM64 construction

Allocation: `broker-fake-child-boundary-4485-arm64-construction-20260928-01`  
Issue #5013's seven-case formal allocation remains unconsumed. This is a one-case construction rung, not a retry or substitute for the formal matrix.

## H / T / D / C / U

- **H:** a real local fake child process exiting 23 is observed by the current-main host broker as exit 23; the broker process propagates 23 while retaining child stdout and emitting a typed non-authoritative receipt.
- **T:** run one actual fake executable through the unchanged broker on a disposable IPC directory. Capture child argv/stdin, broker process exit, response bytes, stderr receipt, source/input hashes. Run a second raw-only auditor that imports neither runner nor broker and rejects eight copied-result mutations.
- **D:** `PASS_REAL_FAKE_CHILD_NONZERO_CONSTRUCTION_SCOPED` only when child call is exactly once, broker and receipt returncodes are exactly 23, response/stderr match, source is unchanged, authority is false, and the independent audit rejects 8/8 corruptions. Any contrary complete behavior is FAIL; missing files/source/runtime identity is STOP.
- **C:** same unchanged broker/image for one request; deterministic fake child; no actual Codex CLI, model/provider, credentials, network, GUI, user data, or authority.
- **U:** one Linux/ARM64/Python 3.12.14 case only. No AMD64 equivalence, timeout/unavailable/malformed/idle/two-queued behavior, real Codex, model/provider, GUI/task effect, latency, runtime authority, or product claim.

## Provenance and environment

- Intake main when inspected: `d092bd3c74dc6b69a630f4d3ae343798129f0899`.
- Additive construction branch `research/broker-fake-child-boundary-4485-arm64-construction-20260928` is created from current main commit `011912b1d2af1af31b3db0b826efadd73fe5cb3b`; no pre-existing branch, PR, comment, or allocation collision was found for this construction ID/path.
- Frozen broker: `runtime/host_model_ipc_broker_v1.py`, Git blob `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`.
- Local OrbStack Docker 29.4.0 Linux/aarch64; `python:3.12-slim-bookworm` config ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, linux/arm64, Python 3.12.14. This explicitly differs from #5013's linux/amd64 formal condition; no cross-architecture inference is made.
- Read-only rootfs/source/input, no network, 0.25 CPU, 256 MiB, 32 PIDs, dropped capabilities, no-new-privileges, 32 MiB tmpfs. Runner output is fresh/writable; auditor sees raw read-only and writes only a separate audit directory.

Exact commands from the workspace root:

```sh
docker run --rm --pull=never --platform=linux/arm64 --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus=0.25 --memory=256m --pids-limit=32 --tmpfs /tmp:rw,nosuid,nodev,size=32m --mount type=bind,src="$PWD/scratch/issue5013_construction_arm64_v1/input",dst=/input,readonly --mount type=bind,src="$PWD/scratch/issue5013_construction_arm64_v1/src",dst=/src,readonly --mount type=bind,src="$PWD/scratch/issue5013_construction_arm64_v1/out",dst=/out --workdir /src --entrypoint python3 python:3.12-slim-bookworm /src/run_probe.py /input /out
docker run --rm --pull=never --platform=linux/arm64 --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus=0.25 --memory=256m --pids-limit=32 --tmpfs /tmp:rw,nosuid,nodev,size=32m --mount type=bind,src="$PWD/scratch/issue5013_construction_arm64_v1/input",dst=/input,readonly --mount type=bind,src="$PWD/scratch/issue5013_construction_arm64_v1/src",dst=/src,readonly --mount type=bind,src="$PWD/scratch/issue5013_construction_arm64_v1/out",dst=/out,readonly --mount type=bind,src="$PWD/scratch/issue5013_construction_arm64_v1/audit",dst=/audit --workdir /src --entrypoint python3 python:3.12-slim-bookworm /src/audit_raw.py /out/RAW_RESULT.json /audit/INDEPENDENT_AUDIT.json 5734f54f318db9ac5e96b2bed6f6bed105ac39ff
```

Runner invocation count 1; retries 0. Auditor is a separate read-only-input container and does not rerun the experiment.
