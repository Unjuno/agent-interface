# Run record — #6695 T0

- Allocation: `REVERSIBILITY-HORIZON-6695-T0-WSLC-20261002-01`
- Preregistration: Issue #6695 comment `5951990931`, posted before formal candidate/audit invocations.
- Intake/freeze parent: `8c06589df01b2c4c1ab4017744faca61cab729f8`
- Branch: `research/reversibility-horizon-6695-t0-wslc-20261002`
- Candidate: `experiment.py`, SHA-256 `06267e52be3248facbd623e549a388b46f85bc32a75b328560b15503e4c01860`
- Auditor: `audit.py`, SHA-256 `4761ef52e4f88325e48333a6ece511c9419d9894232423154433a14ef21131d8`
- Runtime: WSL 3.0.1.0 / Arch Linux / native WSLc / Python 3.12.15.
- Image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; local image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`.
- Limits requested: pull never, network none, CPU 1, memory 512 MiB. Runtime warning: kernel does not support swap-limit capabilities or cgroup is not mounted; effective cap not asserted.

## Commands and outcomes

Construction (before freeze), exit 0, six tests passed:

```text
wslc run --rm --pull never --network none --cpus 1 --memory 512m --mount type=bind,source=<worktree>,target=/work --workdir /work/research/analysis/reversibility_horizon_6695_t0_20261002 python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -m unittest -v test_reversibility_horizon.py
```

Formal candidate, one invocation, exit 0:

```text
python experiment.py --out results/formal_01/candidate/raw.jsonl
```

Independent raw-only auditor, one invocation, exit 0; summary `PASS_SCOPED`, 12 rows, zero errors:

```text
python audit.py results/formal_01/candidate/raw.jsonl --out results/formal_01/auditor/audit.json
```

Both formal commands ran in separate fresh native WSLc containers from the pinned local image with pull disabled, no network, CPU 1 and 512 MiB requested. Each emitted the same cgroup/swap enforcement warning. Candidate retries: 0; auditor retries: 0; replacement IDs: 0.

## Immutable outputs

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `results/formal_01/candidate/raw.jsonl` | 5,294 | `11cccbbe6b401e1ec2cabf6f8dceb96d9b855da8896756c3eb6ea766a91f0dea` |
| `results/formal_01/auditor/audit.json` | 1,513 | `74cbf4f986098e9d9bf169187d08e79a7cfceece7324fc174ab4d7d8383c9865` |

The raw retains each transition. Audit counts are one row per stratum/policy. All four decision gates are true; errors list is empty. No outputs were overwritten or rerun.

## Post-run documentation clarification

After the formal run, README.md's present-tense pre-run status was updated to point to REPORT.md and clarify that the listed formal commands are reproduction instructions, not authorization to rerun. The frozen pre-run README bytes remain in the parent commit and had SHA-256 `91283975a52b73f54abaa85d7a8dfea9ffb3c28d9ff670538d4442c20284f05f`. No hypothesis, schedule, decision gate, candidate, auditor, test, or raw output was changed. This follow-up is documentation-only and does not amend the allocation result.
