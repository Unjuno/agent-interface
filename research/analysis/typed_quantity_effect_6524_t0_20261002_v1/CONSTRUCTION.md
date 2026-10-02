# Construction evidence (not formal result)

- Host: CPython 3.11.9.
- Host command: `python -m unittest discover -s research/analysis/typed_quantity_effect_6524_t0_20261002_v1 -p test_quantity.py -v`
- Host result: 7/7 passed, 0.003 s.
- WSLc: 3.0.1.0; Python 3.12.14, linux/amd64; image digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`.
- WSLc command:

```powershell
$src=(Resolve-Path .\research\analysis\typed_quantity_effect_6524_t0_20261002_v1).Path
wslc.exe run --rm --pull never --network none --cpus 0.25 --volume "${src}:/src:ro" --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python3 -B -m unittest discover -s /src -p test_quantity.py -v
```

- WSLc result: 7/7 passed, 0.010 s. The source was mounted read-only; network disabled; no `--gpus` flag and no memory cap/claim.
- Before construction, read-only `wslc ps` showed no running WSLc containers. The cached pinned image was inspected and its RepoDigest matched the frozen digest.
- One construction-only WSLc container was run and auto-removed. It is not a candidate or auditor formal invocation.
- One earlier host construction attempt failed at module import while the package was incomplete. It ran no formal candidate or auditor.

No Docker Desktop, model, CUDA, GUI, private data, external effect or network use occurred. The formal one-shot counts remain 0 candidate / 0 auditor / 0 retry at preregistration.
