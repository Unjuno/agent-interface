# A06 exact WSLc invocations

The original A05 candidate is not rerun. The immutable input is the copied A05 raw JSON whose SHA-256 is frozen in FREEZE.json. Candidate checker and independent checker are separate containers.

## Candidate-side exact-set and tamper tests

~~~powershell
$pkg=(Resolve-Path 'research\doom\scorer_feedback_attribution_59_t0_a06_20261004').Path
$out=(Resolve-Path "$pkg\out\candidate").Path
wslc run --name ai59-vocab-a06-candidate-20261004 --pull never --network none --cpus 1 --memory 128m --user 65534 --env PYTHONDONTWRITEBYTECODE=1 --env A06_RAW_INPUT=/src/parents/a05-candidate.raw.json --env A06_OUT=/out/candidate.raw.json --mount "type=bind,source=$pkg,target=/src,readonly" --mount "type=bind,source=$out,target=/out" --workdir /src sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364 sh -c 'python -m unittest discover -s /src/tests -v && python /src/audit_candidate.py'
~~~

## Separate raw-only independent audit

~~~powershell
$pkg=(Resolve-Path 'research\doom\scorer_feedback_attribution_59_t0_a06_20261004').Path
$raw=(Resolve-Path "$pkg\parents").Path
$out=(Resolve-Path "$pkg\out\audit").Path
wslc run --name ai59-vocab-a06-auditor-20261004 --pull never --network none --cpus 1 --memory 128m --user 65534 --env PYTHONDONTWRITEBYTECODE=1 --env A06_RAW_INPUT=/input/a05-candidate.raw.json --env A06_AUDIT_OUT=/out/audit.raw.json --mount "type=bind,source=$pkg,target=/src,readonly" --mount "type=bind,source=$raw,target=/input,readonly" --mount "type=bind,source=$out,target=/out" --workdir /src sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364 sh -c 'python /src/audit_independent.py'
~~~

Before the invocations, WSLc inventory confirmed the two names above were unused and the exact cached image ID was present. Retain the raw stdout and inspect output; do not retry a failed invocation.
