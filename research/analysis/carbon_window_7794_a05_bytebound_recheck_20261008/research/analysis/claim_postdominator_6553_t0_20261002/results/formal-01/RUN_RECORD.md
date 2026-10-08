# Formal allocation run record

- Allocation: `CLAIM-POSTDOMINATOR-6553-T0-WSLC-20261002-01`
- Source base: main `18b6e3e084db23d516711442fe39a1d6d34f5765`
- Candidate source/input hashes and full preregistration: parent `FREEZE.json`
- Runtime: WSLc 3.0.1.0; cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
- Pull `never`; network `none`; CPU 1; memory `512m`; source bind mount read-only; separate result bind mount writable; containers `--rm`.
- Effects excluded: GUI, model/API, game, GPU, physical input, and external application effects.

## Candidate

One invocation, exit 0, stdout: `{"status": "CANDIDATE_COMPLETE", "case_count": 7, "output": "/out/raw.json"}`. The exact command was:

```text
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512m --mount type=bind,source=<allocation>,target=/src,readonly --mount type=bind,source=<results>,target=/out --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/candidate.py --fixture /src/fixture.json --out /out/raw.json
```

## Independent auditor

Because candidate exit was 0, one separate auditor invocation was made; exit 0,
stdout: `{"status": "PASS_METHOD_SCOPED", "error_count": 0, "output": "/out/audit.json"}`. No retries or additional candidate/auditor invocations.

```text
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512m --mount type=bind,source=<allocation>,target=/src,readonly --mount type=bind,source=<results>,target=/out --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/auditor.py --fixture /src/fixture.json --oracle /src/oracle.json --raw /out/raw.json --out /out/audit.json
```

Both invocations emitted this WSLc diagnostic:

```text
wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.
```

Therefore the memory flag was accepted and WSLc reported memory limited, but
cgroup/swap enforcement is not independently verified. This warning did not
cause a runtime failure. The bounded finite computation completed successfully;
no memory-performance inference is made.

## Result summary

| Case | Independent disposition | Claim paths (candidate / oracle) | Typed cost | Route-local cost |
|---|---|---:|---:|---:|
| positive shared | PASS_TYPED_SHARED | 2 / 2 | 3.0 | 6.0 |
| bounded loop, no gain | NO_COMPRESSION_GAIN | 3 / 3 | 6.0 | 6.0 |
| wrong target | UNKNOWN_NO_SOUND_SHARED_CHECK | 1 / 1 | — | — |
| stale generation | UNKNOWN_STALE_CHECK | 1 / 1 | — | — |
| hidden effect | UNKNOWN_NO_SOUND_SHARED_CHECK | 2 / 2 | — | — |
| incomplete graph | HOLD_GRAPH_INCOMPLETE | 2 / 3 | — | 6.0 |
| early claim | HOLD_EARLY_CLAIM | 1 / 1 | — | — |

For the positive case the graph-only cut selected `dispatch_ack` at cost 1.5,
but the independent auditor marked it semantically unsound. It was not counted
as claim evidence.

`raw.json` SHA-256:
`b8be792c3453304ccf67883a5ae1bdb8f5dd220b36f79457aa9a917396d94393`

`audit.json` SHA-256:
`ec87f1133ef2a50a3fbfa8bb686aa1a0c5bd834700bf62500211b71048f7d531`

The eight construction/corruption tests were rerun after the formal allocation:
all passed. They did not invoke the formal candidate or auditor.
