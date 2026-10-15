# Reproduction

Run from the repository root on the recorded Windows/WSL host. This is a record of the already-consumed one-shot construction run; do not rerun it as a retry. Construction repair/repetition requires a new ID, a new preregistration and a separate output path.

```powershell
wslc run --rm --name codex-wslc-pr8857-xvfb-a18-20261013 --pull never --network none --cpus 1 --memory 512M --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "<study>/INPUT:/src:ro" --volume "<study>/results/a18-01:/out:rw" --workdir /src/research/doom sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592 python experiment_candidate.py
```

The raw candidate output and exit status are retained under `results/a18-01/`. Re-run only the independent auditor against the saved raw if needed:

```powershell
python -B .\research\doom\v39_pr8857_wslc_xvfb_receipt_a18_20261013\audit.py
```
