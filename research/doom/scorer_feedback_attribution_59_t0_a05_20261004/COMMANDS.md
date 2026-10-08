# A05 exact WSLc invocations

Commands below ran from `repo/work/research-59-scorer-vocab-a05-main-20261004`. Candidate and auditor were separate one-shot containers. The empty WSLc inventory was checked immediately before the candidate; the candidate exited before the auditor started.

## Candidate

```powershell
$pkg=(Resolve-Path 'research\doom\scorer_feedback_attribution_59_t0_a05_20261004').Path
$out=(Resolve-Path "$pkg\out\candidate").Path
wslc run --name ai59-vocab-a05-candidate-20261004 --pull never --network none --cpus 1 --memory 128m --user 65534 --env PYTHONDONTWRITEBYTECODE=1 --env PYTHONPATH=/src:/src/parents/scorer_feedback_attribution_59_t0_a04_20261004:/src/parents/main --env A05_OUT=/out/candidate.raw.json --mount "type=bind,source=$pkg,target=/src,readonly" --mount "type=bind,source=$out,target=/out" --workdir /src sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364 sh -c 'python -m unittest discover -s /src/parents/scorer_feedback_attribution_59_t0_a04_20261004 -v && python /src/tests/test_a05.py && python /src/run_candidate.py'
```

## Independent raw-only auditor

```powershell
$pkg=(Resolve-Path 'research\doom\scorer_feedback_attribution_59_t0_a05_20261004').Path
$candidate=(Resolve-Path "$pkg\out\candidate").Path
$out=(Resolve-Path "$pkg\out\audit").Path
wslc run --name ai59-vocab-a05-auditor-20261004 --pull never --network none --cpus 1 --memory 128m --user 65534 --env PYTHONDONTWRITEBYTECODE=1 --env A05_RAW_INPUT=/candidate/candidate.raw.json --env A05_AUDIT_OUT=/out/audit.raw.json --mount "type=bind,source=$pkg,target=/src,readonly" --mount "type=bind,source=$candidate,target=/candidate,readonly" --mount "type=bind,source=$out,target=/out" --workdir /src sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364 sh -c 'python /src/audit_raw.py'
```

Raw stdout and `wslc inspect` output are in `out/candidate/` and `out/audit/`. WSLc emitted `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Inspect confirms the requested memory/CPU values and `NetworkMode=none`, but the warning means no swap limit was established and configured limits alone do not prove kernel enforcement. No GPU was passed.
