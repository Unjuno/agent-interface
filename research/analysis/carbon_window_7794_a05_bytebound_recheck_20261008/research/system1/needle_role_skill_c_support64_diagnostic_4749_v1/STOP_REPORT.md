# STOP report — #4767 diagnostic construction

## Disposition

`STOP_AUDIT_AND_PROVENANCE_DEFECT`. One paired local CPU Docker orchestration completed on fresh seed 7866101, but an independent raw-only auditor rejected the retained record because its support-prefix assertion is false. Do not interpret the observed accuracy difference as a scientific result. Do not rerun this seed or repair its raw output in place.

The runner was independently transcribed from the visible #4749 contract and retained #3890 `source/runner.py`. GitHub fetches for #4749's listed root-level `support_formal_builder.py` and `support_loader.py` returned 404, and its public directory listing did not show the README-described `tests/` directory. This is an MCP-visible source/provenance gap; it is not proof those files are absent from the repository. The exact formal builder/loader binding therefore could not be verified from this public main snapshot. The `support16_is_prefix` field in this independently transcribed runner came from an erroneous check against the full 64-row tensor instead of a regenerated 16-row stream. This is retained as a failed construction/audit event, not as an efficacy observation. The parent issue's original seed 7865001 construction audit and result are unchanged and not disputed.

## Immutable local raw and audit

- `RAW.json` SHA-256: `e82cbd35e46a1fcc66e906a6c58a30149e64bcc4d5afbfb15fd92e9247bf5212`
- Raw payload self-hash: `e24eb708ab5de7d1c3beaafa8ac2fba795c46ccf35e447dd82184438134ae9dc`
- Runner source at execution SHA-256: `e33e7be82cf00bbc7fe8f44462382d92fc6729e0c71c505efeb3972af72406f4`
- Raw-only audit source SHA-256: `c6bc73d3f3eca911fd6b403010e64f3387e70ecf5062fdfbb6fabec3894d18ef`
- Independent audit: `HOLD_RAW_RECORD`, error `support_prefix`; training-source replay, Docker invocation binding, and prefix truth from omitted raw inputs were not verified.
- The arithmetic delta in the raw record is intentionally not interpreted as evidence.

## Environment

- Host: Windows x86_64, Docker Desktop Linux engine; host inventory: Intel i7-12700H, ~31.7 GiB RAM, NVIDIA RTX 3080 Laptop 16 GiB.
- Container: `needle-pilot05:local`, immutable ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64, Python 3.12.14, PyTorch 2.5.1+cpu, one CPU thread; NumPy absent warning. CPU only.
- Invocation: `docker run --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=64m ... needle-pilot05:local -B /src/diagnostic.py`.
- No retry, network, package install, provider/model API, GUI, user data, or action authority.

The STOP does not consume or modify #4749's reserved formal seeds. Any follow-up needs resolved provenance and a new independently frozen allocation with a new seed and passing source/pairing checks.