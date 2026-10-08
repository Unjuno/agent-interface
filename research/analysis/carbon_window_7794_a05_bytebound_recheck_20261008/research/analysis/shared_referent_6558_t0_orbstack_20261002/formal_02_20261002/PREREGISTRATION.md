# Allocation 02 preregistration — corrected Docker mount syntax

Allocation: `SHARED-REFERENT-6558-T0-ORBSTACK-20261002-02`.

Allocation 01 is terminal `STOP_DOCKER_RUN_ARGUMENT_REJECTED_BEFORE_CONTAINER_CREATE`; it is not retried. No container or candidate existed in allocation 01. This is a distinct fresh output namespace and prospective execution. Candidate/auditor source, fixtures, truth oracle, question, denominator and decision gates are unchanged; only the mount argument form and allocation identity/output names differ.

Frozen source base: latest fetched main `b538fe9f83a7b3f739887fe500959fd72523c69d`; candidate source tree commit is the commit containing this preregistration and the main sync. The exact candidate/auditor/input hashes are those in the parent `FREEZE.json` and are rechecked before each formal call. Construction tests must pass 5/5 before commit. Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

Fresh host paths: `/tmp/shared-referent-6558-t0b-20261002/candidate` and `/tmp/shared-referent-6558-t0b-20261002/audit`; both must be absent before setup and are created empty. Output bind mounts omit a mode field because Docker bind mounts are writable by default. Source mounts use the supported `readonly` flag. The old allocation 01 path is not reused.

Candidate, at most once:

```sh
docker run --name shref-6558-t0b-candidate-20261002-02 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-02/agent-interface-6558-t0-orbstack/research/analysis/shared_referent_6558_t0_orbstack_20261002/candidate.py,dst=/candidate.py,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-02/agent-interface-6558-t0-orbstack/research/analysis/shared_referent_6558_t0_orbstack_20261002/fixtures.json,dst=/fixtures.json,readonly --mount type=bind,src=/tmp/shared-referent-6558-t0b-20261002/candidate,dst=/out python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /candidate.py /fixtures.json /out/candidate.json
```

Independent auditor, only after candidate exit 0, at most once:

```sh
docker run --name shref-6558-t0b-auditor-20261002-02 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-02/agent-interface-6558-t0-orbstack/research/analysis/shared_referent_6558_t0_orbstack_20261002,dst=/src,readonly --mount type=bind,src=/tmp/shared-referent-6558-t0b-20261002/candidate,dst=/raw,readonly --mount type=bind,src=/tmp/shared-referent-6558-t0b-20261002/audit,dst=/out python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/auditor.py /src/fixtures.json /src/oracle.json /raw/candidate.json /out/audit.json
```

No retries. If either Docker command fails, record the exact output and STOP this allocation. Auditor must be a different container; the candidate never mounts `oracle.json`. Never stop/remove/edit the shared user container `unjuno-native-ci-6092`.

Formal counts at freeze: candidate=0, auditor=0, retries=0. Gate: all 9 case IDs exactly once, all four arms independently reconstructed, all 3 valid source-changing cases re-grounded to hidden intent, 2 invalid evidence cases UNKNOWN, no re-ask in stable or zoom-only cases, attention-only grants no authority, and auditor mutation controls remain red. Failure remains a scoped method FAIL, not grounds for retry.
