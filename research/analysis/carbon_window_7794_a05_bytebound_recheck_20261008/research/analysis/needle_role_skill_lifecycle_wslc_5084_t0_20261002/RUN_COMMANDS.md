# Frozen WSLc invocation contract

Run from PowerShell after the GitHub issue and branch freeze is recorded. The four host paths must resolve to the frozen source directory, the exact seed-3788 builder directory, repository `research/analysis` reference root, and a new empty output directory. `wslc image ls` must show the pinned image locally; do not pull. Confirm `wslc container list --all` has no active owner container and confirm no GPU process is started by this CPU experiment. Keep command stdout/stderr and exit codes beside the mounted output in the host evidence record.

Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

Construction (one container):

```powershell
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 `
  --mount "type=bind,source=$SOURCE,target=/src,readonly" `
  --mount "type=bind,source=$REFERENCES,target=/refs/analysis,readonly" `
  --mount "type=bind,source=$INPUTS,target=/inputs,readonly" `
  --mount "type=bind,source=$CONSTRUCTION_OUTPUT,target=/out" `
  -e "INPUTS_DIR=/inputs" -e "REFERENCE_ROOT=/refs/analysis" `
  -e "PYTHONPATH=/refs/analysis/needle_role_skill_lifecycle_4916_first_rung_v2" `
  -w /src --entrypoint python $IMAGE -B -m unittest -v test_contract
```

Candidate (one container, only after construction PASS): same runtime/source/reference/input binds, but use a fresh formal output directory, set `OUT_DIR=/out` and `CONTAINER_IMAGE_ID=sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, then run `python -B candidate.py`.

Auditor (one separate container, only after candidate exit 0): mount formal output as read-only at `/results`, mount a fresh audit-output directory at `/out`, and run `python -B audit.py --raw /results/raw.json --out /out/audit.json` with the same pinned image, network, CPU, memory, input, and reference options. No command may be retried after it starts. Any failed gate or first invocation outcome is retained unchanged.
