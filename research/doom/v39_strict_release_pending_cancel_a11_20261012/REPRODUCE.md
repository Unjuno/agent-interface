# Reproduction

Run from PowerShell in this package with WSLc 3.0.1.0 and the pinned image digest available locally.

```powershell
$image = 'python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd'
$wslc = 'C:\Program Files\WSL\wslc.exe'
$source = (Resolve-Path .).Path
& $wslc run --rm --pull never --network none --cpus 1 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "${source}:/src:ro" --workdir /src $image python -m unittest -v test_strict_release_pending_cancel_integration
& $wslc run --rm --pull never --network none --cpus 1 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "${source}:/src:ro" --workdir /src $image python -O -m unittest -v test_strict_release_pending_cancel_integration
py -3 .\audit.py
```
