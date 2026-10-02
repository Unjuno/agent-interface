# Docker reconstruction check — Needle Pilot-06 post-hoc strata

Allocation: `needle-pilot06-docker-reconstruction-20261001-01`

This is a containerized reproducibility check of the post-hoc raw reconstruction already integrated on main. It does **not** repeat the Pilot-06 model/training allocation, call a model, read a new seed, or change its formal outcome.

## H / T / D / C / U

- **H:** The stdlib-only `reconstruct.py` result is invariant between the prior host execution and a pinned, isolated local Linux container when the exact immutable raw and corrected audit bytes are supplied read-only.
- **T:** Run the main-integrated script once in local Docker Desktop using the pinned `python:3.12-slim` digest; mount the formal JSON and corrected audit read-only, disable network, make root read-only, cap at 1 CPU / 256 MiB / 32 PIDs, and compare source/input hashes and per-seed/per-band counts.
- **D:** `PASS_RECONSTRUCTION_REPRODUCIBLE` if the container exits 0, raw/audit hashes bind, all 3,072 rows reconstruct, and the exact nine stratum tuples match the earlier host run. Otherwise typed STOP/FAIL; no retry.
- **C:** This validates deterministic post-hoc arithmetic and its packaged runtime only. It does not repeat the independent formal auditor or independently establish the underlying model predictions; those remain bound to Pilot-06's retained raw and corrected audit.
- **U:** One host, one Docker engine/image, one retained synthetic raw. No model quality, new scientific allocation, calibration, GUI/task effect, or production claim.

## Frozen identities and observed execution

- Start main: `1cb035f81a17a8122231c55f4a9eb804fdca40c9`.
- Docker Desktop: `desktop-linux`, server 29.8.0, linux/amd64.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; image inspect confirmed linux/amd64. No pull/build.
- Network: none; root filesystem read-only; raw and audit mounts read-only; limits 1 CPU, 256 MiB, 32 PIDs, 16 MiB noexec/nosuid tmpfs.
- Candidate command: `python /src/reconstruct.py /input/FORMAL_RESULT.json /audit/AUDIT_FINAL.json`.
- Candidate exit: 0. Independent model/audit runner was not invoked.
- Postflight: no running containers.

SHA-256: raw `0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7`; corrected audit `8a922fce11fcbc0daa67683ddf84e21cd99344cef4598546f56dbb49c3fc458f`; main script `075d15f7ef86180774909b76d6b4db3ea50deac49f62805b7cc7fb3c2e42ec9c`.

## Result

Container output matched the prior host output exactly: 3 seeds × 1,024 rows = 3,072. CORRECT proposals were 0/728 for `|dx|∈[0.071,0.090)`, 29/1,222 for `[0.090,0.120)`, and 397/1,122 for `[0.120,0.149)`. Per-seed counts are retained in `RUN.json`.

Pilot-06's formal disposition remains `FAIL_NEAR_BOUNDARY_SHIFT`; this container check does not change it.
