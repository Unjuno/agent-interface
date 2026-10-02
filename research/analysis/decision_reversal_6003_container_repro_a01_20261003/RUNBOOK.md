# #6003 successor: OrbStack container reproducibility A01

**Allocation:** `6003-container-repro-a01-20261003`
**Frozen base:** `94112d59c76f9bcccb3c80582e43a750348ad520`
**Parent:** #6003; host-only predecessor: #6003 comment #5931505537 and Draft PR #6042
**Runtime:** OrbStack Docker Engine 29.4.0, linux/arm64
**Image:** `python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b` (already local; pull/build forbidden)

## H / T / D / C / U

- **H:** The frozen #6003 selector and independent checker, run in isolated OrbStack containers on arm64, reproduce the host predecessor's selector choices and audit invariants exactly. Otherwise retain a scoped runtime divergence or STOP.
- **T:** Use the predecessor's `FREEZE.json` byte-for-byte and selector/checker logic unchanged. Only their output scope/status strings are updated to identify this container reproduction. Run one candidate and then one independent checker in separate containers, with no retries or tuning.
- **D:** Pass only if both commands exit 0, the independent audit has no errors, A is selected by cheapest/nominal entropy, B by robust reversal, B/C entropy order reverses under the declared prior shift, the null control is UNRANKABLE, the hard sentinel remains mandatory, STOP contributes no support, and all rankings/control values equal the predecessor. Retain any mismatch as FAIL/HOLD. Runtime/setup failure before candidate launch is STOP.
- **C:** One synthetic finite table, one macOS/OrbStack arm64 host, one pinned locally present Python image, one candidate run and one independent audit run.
- **U:** This tests only reproducibility of an authored finite selector under one disposable container. It does not establish calibrated priors, useful roadmap decisions, productivity, GUI/runtime behavior, safety effectiveness, or broad cross-platform portability.

## Predecessor and frozen source lineage

The predecessor consumed one host-only candidate and one independent audit. Its evidence remains unchanged:

- Freeze SHA-256: `8ff6c4d5d1594ab4623c52483b0f033a8aa6b5ede7f74ea71809461a9469352b`
- Original selector SHA-256: `f23ce27bed6d9c6de6e29b5715e667783d552ecbd73b049a80fc3e2955e3a316`
- Original auditor SHA-256: `e1bf0aca36389439bcbf693ed775ff038e297d7c0c6d4e5f27fab5916a46d4b2`
- Predecessor candidate result SHA-256: `0a267821274056f87a3c6beace29b50623865382c2fe4dda0d0bba9e150af57b`
- Predecessor independent audit SHA-256: `9a5e32bf1a1e76437d9989e886c263223b35625f77ee0d5ee6e59a9c1f3b78c9`

The fixture bytes are identical. Candidate/auditor code differs from its predecessor only in output metadata labels (see `SOURCE_DIFF.md`); the selector and audit computations are unchanged. The predecessor result was not used as a candidate input; it is an independently retained parity target.

## Isolation and one-shot commands

The working directory is this package. Mount it read-only. Both containers use the same pinned local image, no network, a read-only root filesystem, a 16 MiB temporary filesystem, one CPU, 256 MiB memory, 64 PIDs, no Linux capabilities, and no-new-privileges. The candidate and auditor use separate container IDs. No shared container is inspected or changed.

Candidate:

```sh
docker run --name issue6740-candidate-a01 --pull=never --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 1000:1000 --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-03/agent-interface-6003-container-repro-a01-20261003/research/analysis/decision_reversal_6003_container_repro_a01_20261003,dst=/input,readonly --entrypoint /bin/sh python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b -c 'mkdir -p /tmp/run && cp /input/FREEZE.json /input/select.py /input/audit.py /tmp/run/ && cd /tmp/run && python select.py'
```

After recording exit status and container inspection, copy `/tmp/run/candidate_result.json` from that stopped container into `execution/candidate_result.json`.

Independent auditor (separate container; candidate result is a read-only input):

```sh
docker run --name issue6740-auditor-a01 --pull=never --network=none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 1000:1000 --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-03/agent-interface-6003-container-repro-a01-20261003/research/analysis/decision_reversal_6003_container_repro_a01_20261003,dst=/input,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-03/agent-interface-6003-container-repro-a01-20261003/research/analysis/decision_reversal_6003_container_repro_a01_20261003/execution,dst=/evidence,readonly --entrypoint /bin/sh python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b -c 'mkdir -p /tmp/audit && cp /input/FREEZE.json /input/select.py /input/audit.py /tmp/audit/ && cp /evidence/candidate_result.json /tmp/audit/ && cd /tmp/audit && python audit.py'
```

After recording exit status and container inspection, copy `/tmp/audit/independent_audit.json` into `execution/independent_audit.json`. Retain stdout, exact commands, Docker inspection metadata, and SHA-256 values. Remove only these two named stopped containers after all evidence is copied and hashed.

## Explicit scope boundary

The candidate's result labels the run as container-scoped but does not itself attest container identity. Runtime identity and limits must be supported by the Docker command, image ID, container inspection, and host engine record retained alongside the raw result. This is method reproducibility only; a PASS is not evidence of real-world research utility.

## A01 actual disposition

The one candidate invocation exited 1 before it wrote `candidate_result.json`. Its traceback shows that naming the script `select.py` shadowed Python's standard-library `select` module when `platform.platform()` imported `subprocess`/ `selectors`. This is `FAIL_RUNNER_IMPORT_COLLISION_NO_METHOD_RESULT`; selector rankings were not evaluated. The predeclared mathematical auditor was not invoked because there was no candidate result.

A separate post-hoc raw-trace classifier ran once in another container and returned `PASS_FAILURE_TRACE_CLASSIFICATION`, errors empty. This validates only the retained exception chain, not selector correctness. Its exact stdout was retained; its JSON file was on ephemeral tmpfs and was not recoverable after container exit. The copy failure is disclosed in `execution/FAILURE_TRACE_AUDIT.json`. No retry, replacement candidate, or tuning occurred in A01. Both named containers were stopped; cleanup occurs only after final hashes are recorded.

## Pre-candidate main-advance amendment

The first current-main check found `89c67103de1e3061ff070c62825dac12041c5333`; a second check before candidate launch found preservation-only merge #6210 had advanced main to `94112d59c76f9bcccb3c80582e43a750348ad520`. No candidate or auditor had started. The branch was fast-forwarded to the new main, and this base supersedes the earlier value. The frozen predecessor fixture and selector contract are unchanged.
