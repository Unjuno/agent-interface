# Executed commands

Baseline on the exact parent source (`fbed929f629dabaa9ae752019d0ee7151d4d2298`):

```powershell
python research/doom/map01-v39-release-cleanup-overlap-v1/run_baseline.py
```

Expected and observed: regression test fails because the baseline still marks
the overlapped release ordinary.

Candidate, executed in cached WSLc image
`sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`
with network disabled, one CPU, 512 MiB accepted memory limit, read-only source
and writable evidence output:

```powershell
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume "${repoPath}:/src:ro" --volume "${resultsPath}:/out" --workdir /src `
  sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364 `
  python -B -m unittest -v research.doom.test_doom_typed_release_backend_v3
```

`RAW_CANDIDATE.txt` retains stdout and stderr, including the WSL swap/cgroup
warning. The memory limit was accepted; swap isolation was unavailable.

