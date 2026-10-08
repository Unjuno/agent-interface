# Formal-01 setup-failure record

Base main: `c215b11fc9609ec02810a22317c926374f399858`

Docker Engine: Docker Desktop 28.5.1, Linux/amd64

Image: `python@sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`

Network: disabled

Source/root: read-only

Output: fresh host directory, separate from source

The exact formal command was run once. It omitted `-e PYTHONPATH=/source`:

```powershell
docker run --rm --network none --read-only `
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --cpus 1 --memory 512m --pids-limit 64 `
  --cap-drop ALL --security-opt no-new-privileges `
  --mount "type=bind,source=$repoPath,target=/source,readonly" `
  --mount "type=bind,source=$formalPath,target=/out" `
  --workdir /source `
  -e EXPECTED_COMMIT=c215b11fc9609ec02810a22317c926374f399858 `
  -e "IMAGE_REF=$imageRef" -e OUT=/out `
  --entrypoint python3 $imageRef `
  /source/research/experiments/issue_3814_newline_frame_v1/runner.py
```

Observed exit: nonzero. Error before experiment setup:

```text
ModuleNotFoundError: No module named 'runtime'
```

The formal output directory remained empty. No retry was performed. The preflight import command had set `PYTHONPATH=/source`, which is why preflight passed while the formal command failed; that discrepancy is the setup error preserved here.
