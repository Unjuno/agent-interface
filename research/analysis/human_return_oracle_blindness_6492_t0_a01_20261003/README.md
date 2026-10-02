# #6492 oracle-blind return-cue packets A01

This package tests a strict input-boundary correction to the earlier synthetic #6492 T0. The candidate sees only public view/cue data. Hidden correct-return labels are stored separately for an independent raw-only auditor. This is not a human-resumption or product experiment.

## Construction

Run from the repository root:

```bash
python3 research/analysis/human_return_oracle_blindness_6492_t0_a01_20261003/build_fixture.py \
  --output-root research/analysis/human_return_oracle_blindness_6492_t0_a01_20261003/fixture
python3 -m unittest discover -s research/analysis/human_return_oracle_blindness_6492_t0_a01_20261003/tests -v
```

The fixture builder refuses to overwrite a nonempty output root. Tests use temporary directories and host Python; these are construction checks, not formal candidate/auditor counts.

The allocation-specific OrbStack private-Engine probe is retained under `construction/`. It verified public input visibility, auditor truth absence, read-only input/root filesystems, and cgroup `memory.max=536870912`, `cpu.max=100000 100000`. Its container was auto-removed and did not invoke candidate or auditor code.

## Formal container sequence

See `PREREGISTRATION.md` and `FREEZE.json`. The candidate container mounts only `candidate/` and `fixture/candidate-input/` read-only, plus `results/formal-01/candidate/` as output. It never mounts the auditor directory or `fixture/auditor-input/`. The auditor is a later, separate invocation with its own `auditor/`, public input, auditor-only truth, and candidate output mounts read-only, plus its own output directory. Both use the exact pinned image, `--pull=never`, `--network=none`, one CPU, 512 MiB requested memory, non-root UID, read-only root, and dropped capabilities. They run in an allocation-specific isolated OrbStack VM with a private Engine; the shared OrbStack Engine and its existing containers are not used.

Candidate command:

```text
python /src/candidate.py --input /input/public.json --output /out/candidate.raw.json
```

Auditor command:

```text
python /auditor/audit.py --public /public/public.json --truth /truth/truth.json --candidate /candidate/candidate.raw.json --output /out/audit.json
```

One formal candidate and one formal auditor invocation are allowed, with no retries. The raw files, stdout/stderr, exit statuses, container IDs/inspection metadata, source/image/base hashes, and post-run integrity checks are retained beneath `results/formal-01/`. Construction runs are not promoted to formal evidence.

## Scope

Even `PASS_METHOD_SCOPED` proves only the finite information-boundary and packet contract exercised here. It does not show that a person understands the cue, returns correctly to work, or benefits from an interruption design.
