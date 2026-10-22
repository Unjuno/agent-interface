# Reproduce A15

From PowerShell in this directory:

```powershell
$image = 'python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd'
$wslc = 'C:\Program Files\WSL\wslc.exe'
$source = (Resolve-Path .).Path
& $wslc run --rm --pull never --network none --cpus 1 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "${source}:/src:ro" --workdir /src $image python -m unittest -v test_a15_per_key_release_audit
& $wslc run --rm --pull never --network none --cpus 1 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "${source}:/src:ro" --workdir /src $image python -O -m unittest -v test_a15_per_key_release_audit
py -3 .\audit.py
```

The test reads the retained files only. It does not start Docker game services or call a model.
