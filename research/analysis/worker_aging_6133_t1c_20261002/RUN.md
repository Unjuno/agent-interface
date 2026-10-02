# T1c one-shot run record

- Allocation: `ISSUE6133-WORKER-AGING-T1C-20261002-01`
- Source freeze: base `518918b71599bf6d7fb662aaf6ae332e14d6132f`; `FREEZE.json` SHA-256 `5eca38d012100a560497ec3e30bef9b44517b6a00340fe6b30330be9e61b8731`.
- Runtime: WSLc `3.0.1.0`; cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, linux/amd64, Python 3.12.14.
- Preflight: `wslc container list --all` showed no running containers and one unrelated exited migration-smoke container, which was left unchanged. The exact image was already cached. Post-run inventory showed the same unrelated exited container only; the `--rm` T1c container was absent.
- Requested container options: `--pull never --network none --cpus 1 --memory 512M`; package mounted `/src:ro`, output mounted separately at `/out:rw`.
- Start/end UTC: `2026-10-02T03:38:41.8842799Z` / `2026-10-02T03:38:45.3719578Z`.
- Exact in-container sequence: `python -B -m unittest -v test_audit.py && python -B candidate.py /out/raw.json && python -B audit.py /out/raw.json`.
- Construction suite: 4/4 pass. Candidate: one process, exit 0, 15 cells / 600 rows. Separate raw-only auditor: one process, exit 0, `PASS_METHOD_SCOPED`, 15 cells / 600 rows / zero errors. Retries and source edits after freeze: 0.
- Raw candidate SHA-256: `32db0f79a9d2f9baaf242a85c2a0e523b04017ebced71797f3a971bbbd8b9526`.
- Combined WSLc stdout/stderr log SHA-256: `99fb041c4cf8186a5d4333e85b29802e3a4967cff48005f0987fa9fba972c571`.
- The log includes WSL's warning that swap-limit capabilities/cgroup were unavailable. The requested memory flag was accepted, but effective memory/swap enforcement is not claimed.

The retained raw file and complete combined container log are in [`results/t1c-one-shot-01/`](results/t1c-one-shot-01/). No candidate, auditor, source, or formal allocation was rerun after this result.
