# Reproduce A24

Do not rerun into the retained output directory. One-shot command:

```powershell
wslc run --rm --name codex-wslc-v39-backend-xvfb-a24-20261013 --pull never --network none --cpus 1 --memory 512M --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "<study>\INPUT:/src:ro" --volume "<study>\results\a24-01:/out:rw" --workdir /src/research/doom sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592 python experiment_candidate.py
```

Independent auditor: `python audit.py`. Expected result: `PASS_METHOD_SCOPED`.
