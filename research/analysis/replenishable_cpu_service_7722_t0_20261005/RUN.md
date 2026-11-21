# Run record — CPU-CONTROL-7722-T0-20261005-01

## Formal invocation ledger

| Stage | Invocations | Exit | Wall time | Retry |
|---|---:|---:|---:|---:|
| Candidate | 1 | 0 | 0.808 s | 0 |
| Independent auditor | 1 | 0 | 3.933 s | 0 |

Both were fresh WSLc containers named `cpu-control-7722-t0-candidate` and `cpu-control-7722-t0-auditor`, removed on normal completion (`--rm`). Candidate CID: `d1d911d349b4a0cc1a7a9fbfa8a47635509ad9cff625300829c78dab3e7c8829`; auditor CID: `d5402dbef65a584754e388a8ec2a6714dd735941c85fe630b32070caff070c35`. Image is the cached amd64 `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`). WSLc was 3.0.1.0, kernel 6.18.40.1-1.

## Commands

Candidate command used a read-only study mount and its distinct writable output mount:

```powershell
wslc.exe run --rm --cidfile <study>\output\candidate\container.cid --name cpu-control-7722-t0-candidate --pull never --network none --cpus 1 --memory 256m --mount "type=bind,source=<study>,target=/input,readonly" --mount "type=bind,source=<study>\output\candidate,target=/out" --workdir /input --entrypoint /bin/sh python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 -c 'python -B /input/candidate.py --cases /input/cases.json --freeze /input/freeze.json > /out/candidate.raw.json 2> /out/candidate.stderr.log'
```

The auditor ran once in a separate fresh container. Its study and candidate-output mounts were read-only; its audit-output mount was writable:

```powershell
wslc.exe run --rm --cidfile <study>\output\auditor\container.cid --name cpu-control-7722-t0-auditor --pull never --network none --cpus 1 --memory 256m --mount "type=bind,source=<study>,target=/input,readonly" --mount "type=bind,source=<study>\output\candidate,target=/candidate,readonly" --mount "type=bind,source=<study>\output\auditor,target=/out" --workdir /input --entrypoint /bin/sh python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 -c 'python -B /input/auditor.py --cases /input/cases.json --freeze /input/freeze.json --raw /candidate/candidate.raw.json > /out/audit.json 2> /out/auditor.stderr.log'
```

The literal Windows bind-mount paths, CIDs, exit codes, elapsed times, and host file timestamps are retained in each `output/*/run-meta.json`; command forms above use placeholders for those paths. File timestamps are host artifact timestamps, not claimed scheduler start/end timestamps. No image was pulled. Both invocations emitted this WSLc warning, retained byte-for-byte in their `wslc.stderr.log`: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` No running WSLc containers were present immediately before candidate launch or after the two `--rm` runs. No existing image/container was modified or removed.

## Raw and audit outcomes

`output/candidate/candidate.raw.json` is the candidate's unedited stdout. `output/auditor/audit.json` is the separate auditor's unedited stdout: `METHOD_PASS_SCOPED`, `FAIL_HYPOTHESIS`, no audit errors, and six mutation controls rejected. Candidate stderr and auditor stderr were empty. Neither formal process was repeated.
