# Reproduction

The exact controller snapshots and test files used are in `inputs/main/` and `inputs/candidate/`. The source manifest records SHA-256, byte lengths, and Git blob IDs. Run from PowerShell in this directory with WSLc 3.0.1.0 and the cached image digest recorded in `RUN.json`.

```powershell
$image = 'python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd'
$wslc = 'C:\Program Files\WSL\wslc.exe'
$modules = 'test_v39_terminal_release_receipt_completeness test_v39_stale_initial_cover_release_composition test_v39_release_preflight'
$source = (Resolve-Path .\inputs\candidate).Path
& $wslc run --rm --pull never --network none --cpus 1 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "${source}:/src:ro" --workdir /src $image python -m unittest -v test_v39_terminal_release_receipt_completeness test_v39_stale_initial_cover_release_composition test_v39_release_preflight
& $wslc run --rm --pull never --network none --cpus 1 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "${source}:/src:ro" --workdir /src $image python -O -m unittest -v test_v39_terminal_release_receipt_completeness test_v39_stale_initial_cover_release_composition test_v39_release_preflight
py -3 .\audit.py
```

To reproduce the baseline contrast, set `$source = (Resolve-Path .\inputs\main).Path` and run the normal test command. It is expected to fail during test-module import because current-main source does not define `terminal_release_is_known_empty`; it does not reach unittest collection. Do not interpret that import failure as execution of every candidate assertion against old behavior.
