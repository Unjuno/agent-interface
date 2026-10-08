# Durable-fixture broker path rejection — #4937

## H / T / D / C / U

- **H:** Retaining the exact repo/outside fixture tree lets a separate auditor verify actual symlink containment and broker `serve()` receipts after the formal runner exits.
- **T:** One new allocation, `broker-path-durable-fixture-4937-20260928-01`, on local Docker Desktop Linux/amd64. Tested current-main production broker blob `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`; the additive candidate replaces only host path resolution with #4876's resolver and maps resolver errors to authority-free rejection receipts. Pinned image `python:3.13-slim@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0`; network none, source/root read-only, 16 MiB private /tmp, 1 CPU, 256 MiB, 32 PIDs. One actual `serve()` call per isolated request; `subprocess.run` is an in-process recorder. A second networkless/read-only container audited the retained raw, manifest, and fixture tree at the identical `/out` path.
- **D:** `PASS_DURABLE_FIXTURE_SERVE_REJECTION_SCOPED`. 23/23 rows reconciled: 5 accepted aliases/in-root symlinks mapped to canonical in-root argv and each called the mock once; 18 invalid cases across six classes × schema/image/working yielded `InvalidHostPath` / `HOST_MODEL_PATH_REJECTED`, `returncode=null`, authority false, and zero mock calls. Fixture inventory was unchanged from pre-run to post-run. Independent auditor recomputed lstat, file hashes and readlink targets, confirmed three in-root and three external symlinks, and returned errors=[]. Corruption controls: 7/7 rejected.
- **C:** Relative to #4921, the path matrix and candidate policy are held fixed; the new evidence factor is persistence of the actual fixture tree and independent post-run lstat/readlink verification. #4921's raw, audit exception, and HOLD are preserved unchanged.
- **U:** Candidate-bound Linux/Docker construction/integration evidence only. No production runtime patch, actual host CLI/model/provider, host-file read through broker, GUI/task input, GPU use, Windows parity, exploitability, or #3152 live model/task acceptance.

## Provenance and raw results

- Formal runner invocations: 1; retries: 0; post-freeze tuning: 0.
- Main snapshot: `22f14899aba9a942c2de1ce6624e8d785e36553e`; exact production source blob: `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`.
- Raw SHA-256: `661dd8ef8f08257ad641b0973b8cb5ea12db020f68c817b0bc28424aa442a953`.
- Fixture-manifest SHA-256: `8c1698c53d17e7f542e9150ffc144c7954fca7a9f8d01faaaf5ae0e177bd3e3d`.
- Independent audit SHA-256: `370ce3db51f273a6194db9570ee372102d3abadc56e880a16480c63f8c07b413`.
- All source blob IDs/SHA-256 and pre-execution decision gates are in [FREEZE.json](FREEZE.json).

## Reproduction

First run `python runner.py /out/RAW.json /out/FIXTURE_MANIFEST.json` in the frozen bounded runner container. Then run `python audit_raw.py /out/RAW.json /out/FIXTURE_MANIFEST.json /audit/AUDIT.json` in a separate network-disabled/read-only container with the evidence volume mounted read-only at `/out` so the recorded fixture paths remain valid. Exact commands and limits are frozen in FREEZE.json.
