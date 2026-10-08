# STOP report — #4767 diagnostic construction

## Disposition

`STOP_AUDIT_RECORD_DEFECT`. One paired local CPU Docker orchestration completed on fresh seed 7866101, but an independent raw-only auditor rejected the retained record because its support-prefix assertion is false. Do not interpret the arithmetic accuracy delta as a scientific result. Do not rerun this seed or repair its raw output in place.

The execution used an independently transcribed runner based on #4749's public contract and the retained #3890 source. The prefix assertion mistakenly compared the first 16 rows against the full 64-row tensor. The exact runner and auditor source bytes are now retained and match their recorded execution SHA-256 values. The exact #4749 formal builder, loader, and root-level tests were also found on main; the earlier STOP report's MCP-fetch-gap statement was incorrect and has been removed. This remaining STOP is caused solely by this diagnostic record's failed prefix control and limited raw-only evidence. The original #4749 construction seed 7865001 audit/result is unchanged and not disputed.

## Immutable raw and audit

- `RAW.json` SHA-256: `e82cbd35e46a1fcc66e906a6c58a30149e64bcc4d5afbfb15fd92e9247bf5212`
- Raw payload self-hash: `e24eb708ab5de7d1c3beaafa8ac2fba795c46ccf35e447dd82184438134ae9dc`
- Execution runner SHA-256: `e33e7be82cf00bbc7fe8f44462382d92fc6729e0c71c505efeb3972af72406f4`
- Execution raw-only auditor SHA-256: `c6bc73d3f3eca911fd6b403010e64f3387e70ecf5062fdfbb6fabec3894d18ef`
- Final independent audit: `HOLD_RAW_RECORD`, sole error `support_prefix`; the audit does not independently regenerate/retrain the model or verify prefix truth from omitted raw inputs.
- No scientific direction is inferred from the arithmetic delta.

## Environment

- Host: Windows x86_64, Docker Desktop Linux engine; host inventory: Intel i7-12700H, ~31.7 GiB RAM, NVIDIA RTX 3080 Laptop 16 GiB.
- Container: `needle-pilot05:local`, immutable ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64, Python 3.12.14, PyTorch 2.5.1+cpu, one CPU thread; NumPy absent warning. CPU only.
- One invocation only: `docker run --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m ... needle-pilot05:local -B /src/diagnostic.py`.
- Raw-only auditor separately ran in the same pinned, networkless Docker image with 1 CPU, 512 MiB, 32 PIDs, read-only source/raw mounts; exit code 1 is the expected fail-closed result for `support_prefix`.
- No retry, network, package installation, provider/model API, GUI, user data, or action authority.

The STOP does not consume or modify #4749's reserved formal seeds 7865101–7866001. Any future diagnostic requires a new seed, correct pairing test, and independent source-bound audit.
