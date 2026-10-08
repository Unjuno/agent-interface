# Frozen allocation record

- Issue: #5329, freeze comment #5924039650.
- Allocation: `5329-backward-slice-t0-20261001-01`.
- Main base: `5ff239141f49c1603c0f6b078268f4a2f6e082df`.
- Branch: `research/5329-backward-slice-t0-20261001-v2`.
- Runner SHA-256: `CA73B33EF3B7483F3A5CC9ECD0354B91401873FF6F9C7FED87B42BA11581AA7F`.
- Auditor SHA-256: `2BA795477E23085FF2BB0D46D2FA6A50DF98D6CF486B609A06F8C0DA0CE49A50`.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Limits: network none; CPU 1; memory 256 MiB; pids 64.
- Formal output: `results/formal01/`.
- Runner invoked once, exit 0. Independent auditor invoked once after runner exit 0, exit 1. Retries: 0.

Source AST preflight passed before freeze in the same pinned Docker image. The
formal runner command was:

```powershell
docker run --rm --network none --cpus=1 --memory=256m --pids-limit=64 `
  -v "<package>:/src:ro" -v "<outputs>:/out" `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  python /src/runner.py
```

The raw output directory did not exist at invocation. The audit command mounted
the raw read-only and source package read-only in a second network-disabled,
CPU-limited container. Exact runner output and audit exception are retained
with the disposition. The raw file was not edited after generation.
