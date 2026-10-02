# One-shot container command record

Image identity was checked before candidate execution and again before the conditional auditor. Both commands used Docker context `orbstack`, `--pull=never`, `--platform linux/arm64`, `--network none`, `--read-only`, `--cap-drop ALL`, `--security-opt no-new-privileges`, `--cpus 0.5`, `--memory 256m`, `--pids-limit 32`, `--user 501:20`, and `--rm`. The frozen source tree was mounted read-only. Candidate output alone was writable; the auditor's output mount was read-only.

Candidate command:

```sh
docker --context orbstack run --rm --name actuated-info-6045-t0-20261002-01-candidate --pull=never --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop ALL --security-opt no-new-privileges --cpus 0.5 --memory 256m --pids-limit 32 --user 501:20 --mount type=bind,source="$PWD",target=/study,readonly --mount type=bind,source="$PWD/results/OPPORTUNITY-CONDITIONED-ACTUATED-INFO-6045-T0-20261002-01/output",target=/out --workdir /study python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b python -B run_candidate.py fixture.json /out
```

Candidate exit receipt is `candidate.exit` (0); stdout includes `CANDIDATE_COMPLETE`, 18 rows, and raw/fixture/source digests.

Conditional independent auditor command (only after candidate exit 0):

```sh
docker --context orbstack run --rm --name actuated-info-6045-t0-20261002-01-auditor --pull=never --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop ALL --security-opt no-new-privileges --cpus 0.5 --memory 256m --pids-limit 32 --user 501:20 --mount type=bind,source="$PWD",target=/study,readonly --mount type=bind,source="$PWD/results/OPPORTUNITY-CONDITIONED-ACTUATED-INFO-6045-T0-20261002-01/output",target=/input,readonly --workdir /study python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b python -B independent_audit.py fixture.json /input/ledger.jsonl /input/candidate_manifest.json
```

Auditor exit receipt is `auditor.exit` (0); stdout is `{"errors": [], "status": "PASS_METHOD_SCOPED"}`. Each container was auto-removed at exit. No retry or inspection of existing containers/VMs occurred.
