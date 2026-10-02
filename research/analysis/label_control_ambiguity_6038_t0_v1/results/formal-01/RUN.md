# Formal run 01 — preregistered execution record

Allocation: `LABEL-CONTROL-AMBIGUITY-6038-T0-20261002-01`

Issue: #6038

Frozen base: `d7e20a0d25e0c361d1e7cf56fd103f61fb927a2d`

Branch: `research/label-control-ambiguity-6038-t0-20261002`

## Before run

- OrbStack context: `orbstack`; service responsive.
- Existing running containers observed, untouched: `unjuno-native-ci-6092` (`python:3.12-slim`).
- Cached image: `python:3.12-alpine`, ID `sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`, `linux/arm64`; `--pull=never`.
- Candidate source SHA-256: `7d0a7fb4af45baa05dccd5c12ac7bb33f069506af4461a5aeed9d024bd09301f`.
- Auditor source SHA-256: `f338adf365d0a7900dd73499d52ef82dcd2f61f2047b14e1770ab5a94c0f438f`.
- Visible fixture SHA-256: `e5711345d7fe28b14df661006d1d99183d4458719afcaa5735064bff4016fa5f`.
- Hidden effect oracle SHA-256: `e747a71b49c925ce5a8969f93c5f44986cc1fe4d56f46d0ab87d812d153ba50b`.
- Local construction tests passed 4/4 before formal execution; no formal outputs existed.

## Frozen commands

The candidate container receives only `candidate.py` and `fixture.json`. Its stdout is the immutable candidate raw JSON. The separate auditor container receives only `audit.py`, both frozen inputs, and candidate raw; it does not receive candidate source. Its stdout is the independent audit JSON. Both container root filesystems and all input mounts are read-only.

```sh
docker --context orbstack run --rm --pull=never --name ai-6038-t0-candidate-20261002-01 \
  --network none --cpus=1 --memory=256m --pids-limit=64 --read-only \
  --cap-drop=ALL --security-opt=no-new-privileges --user 65532:65532 \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/candidate.py",dst=/src/candidate.py,readonly \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/fixture.json",dst=/input/fixture.json,readonly \
  python /src/candidate.py /input/fixture.json
```

```sh
docker --context orbstack run --rm --pull=never --name ai-6038-t0-auditor-20261002-01 \
  --network none --cpus=1 --memory=256m --pids-limit=64 --read-only \
  --cap-drop=ALL --security-opt=no-new-privileges --user 65532:65532 \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/audit.py",dst=/src/audit.py,readonly \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/fixture.json",dst=/input/fixture.json,readonly \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/oracle.json",dst=/input/oracle.json,readonly \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/results/formal-01/candidate.raw.json",dst=/input/candidate.raw.json,readonly \
  python /src/audit.py /input/fixture.json /input/oracle.json /input/candidate.raw.json
```

## Terminal STOP

At 2026-10-02 07:52:58 JST the frozen Docker command exited 126 before the candidate interpreter started. The invocation omitted the image operand `python:3.12-alpine`; Docker interpreted the next token `python` as the image and attempted to execute `/src/candidate.py` directly. The daemon reported a platform warning for that unintended local image and `exec: "/src/candidate.py": permission denied`. The container auto-removed. Candidate program invocations: 0; auditor invocations: 0; formal command attempts: 1; retries: 0. Candidate stdout is empty (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`); stderr SHA-256 `6674dedc7d05493ddefafc36b8e982ca7519ca1d4cd10755d0284b0388a88315`; exit file SHA-256 `703d2c10fa601276a4dd96193faed68902a642a44eb5b01b40d6fc8499e12822`. Disposition: `STOP_CANDIDATE_CONTAINER_ENTRYPOINT`; this is a launcher failure, not a method result. No retry or audit was made under this allocation. A distinct successor allocation with corrected explicit image argv is recorded in `FREEZE_v2.json` and `results/formal-02/RUN.md`; this STOP and its files remain unchanged.
