# Reproduce A21

This is a one-shot record; do not rerun the candidate into this output directory. The preserved run command was:

```powershell
wslc run --rm --name codex-wslc-pr8874-xvfb-a21-20261013 --pull never --network none --cpus 1 --memory 512M --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "<study>\INPUT:/src:ro" --volume "<study>\results\a21-01:/out:rw" --workdir /src/research/doom sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592 python experiment_candidate.py
```

The auditor is read-only over the saved raw and frozen source tree: `python audit.py`. Expected outcome is `FAIL_ANALYZER_BRIDGE`, not a successful analyzer measurement.
