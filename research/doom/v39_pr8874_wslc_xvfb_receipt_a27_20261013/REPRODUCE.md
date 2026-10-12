# Reproduce A27

Single preregistered candidate run; do not rerun into the retained output directory:

```powershell
wslc run --rm --name codex-wslc-v39-cancel-xvfb-a27-20261013 --pull never --network none --cpus 1 --memory 512M --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "<study>\INPUT:/src:ro" --volume "<study>\results\a27-01:/out:rw" --workdir /src/research/doom sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592 python experiment_candidate.py
```

Run the independent auditor with `python audit.py`; expected decision is `PASS_METHOD_SCOPED`.
