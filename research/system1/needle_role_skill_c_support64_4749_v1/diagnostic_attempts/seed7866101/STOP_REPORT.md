# STOP report — #4767 diagnostic construction

## Disposition

`STOP_AUDIT_RECORD_DEFECT`. One paired local CPU Docker orchestration completed on fresh seed 7866101, but an independent raw-only auditor rejected the retained record because its support-prefix assertion is false. Do not interpret the arithmetic accuracy delta as a scientific result. Do not rerun this seed or repair its raw output in place.

The execution used an independently transcribed runner based on #4749's public contract and retained #3890 source. The prefix assertion mistakenly compared the first 16 rows against the full 64-row tensor. The exact runner and auditor source bytes are now retained and match their recorded execution SHA-256 values. #4749's formal builder, loader, and root-level tests were verified on main; an earlier MCP-fetch-gap statement in the report was incorrect and has been withdrawn. The remaining STOP is the failed prefix control in this diagnostic record and its raw-only audit limitations. The original #4749 seed 7865001 construction audit/result remains unchanged and is not disputed.

## Immutable evidence

- Raw SHA-256: `e82cbd35e46a1fcc66e906a6c58a30149e64bcc4d5afbfb15fd92e9247bf5212`; raw self-hash: `e24eb708ab5de7d1c3beaafa8ac2fba795c46ccf35e447dd82184438134ae9dc`.
- Exact execution runner SHA-256: `e33e7be82cf00bbc7fe8f44462382d92fc6729e0c71c505efeb3972af72406f4`.
- Exact execution auditor SHA-256: `c6bc73d3f3eca911fd6b403010e64f3387e70ecf5062fdfbb6fabec3894d18ef`.
- Final Docker raw-only audit: `HOLD_RAW_RECORD`, sole error `support_prefix`. It does not replay training or independently reconstruct omitted inputs.
- Arithmetic delta is not interpreted.

## Runtime

Windows x86_64 / Docker Desktop Linux; Intel i7-12700H, ~31.7 GiB RAM, NVIDIA RTX 3080 Laptop 16 GiB. CPU-only container `needle-pilot05:local`, image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64, Python 3.12.14, PyTorch 2.5.1+cpu; one thread, NumPy missing warning. One isolated formal orchestration; separate read-only raw-only audit exited 1 as expected for fail-closed detection. No retry, egress, install, provider/API, GUI, user data, or action authority.

Formal seeds 7865101–7866001 remain untouched. Any future diagnostic requires a new seed and corrected pairing test; this failed allocation is not rerun.
