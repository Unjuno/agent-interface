# Issue #8466 T0 A01 preregistration

Allocation: `NEGATIVE-HANDOFF-EXPIRY-5865-T0-A01-20261008`  
Frozen base: `main@1aaa633c4f1aeec25e4b4617d92dd93af3b20603`  
Issue: https://github.com/Unjuno/agent-interface/issues/8466  
Package: `research/analysis/negative_handoff_expiry_5865_t0_a01_20261008/`

## H / T / D / C / U

- **H:** Forwarding a scoped negative receipt must not renew its source-time expiry. A source-bound absolute deadline should reject a late forwarded receipt, while a genuine source re-evaluation with a new epoch/deadline may be accepted.
- **T:** Ten finite source-bound cases exercise timely handoff, late multi-hop handoff, fresh source reevaluation, untrusted clock, stale epoch, query mismatch, scope mismatch, exact-expiry boundary, forwarded timeout, and missing source expiry. Candidate output retains the decision at every handoff. Compare source-time expiry with the deliberately unsafe receiver-relative sliding-TTL control. Candidate receives only `candidate_inputs.json`; the expected dispositions in `oracle.json` remain auditor-only. Candidate runs once; the raw-only auditor runs once only after candidate exit 0. Six effective corruption controls are frozen in the auditor. No action, model, GUI, user data, or network.
- **D:** `PASS_METHOD_SCOPED` only if all 10 raw rows and every hop exactly reconstruct, the candidate gives the frozen disposition per arm, case C02 exhibits the late sliding-TTL false acceptance while the absolute arm expires, the source-re-evaluated case passes under epoch 2, all invalid/unknown cases fail closed, timeout remains typed, authority is false, and all six output mutations are rejected. Any false negative certificate is `FAIL_METHOD`; source, runtime, or audit integrity failure is `STOP`/`HOLD`, never a scientific pass.
- **C:** A receiver's fresh independent source query is a new evaluation, not a forwarded receipt. Clock-authenticity and cross-domain conversion are not tested. A trusted translated monotonic deadline may be less conservative.
- **U:** Logical-time finite model only. No real cache, clock synchronization, live inventory producer, GUI, task outcome, latency, or safety evidence.

## Frozen environment and one-shot commands

- Host: macOS arm64; OrbStack Docker context `orbstack`, Engine 29.4.0, Linux/arm64 VM, cgroup v2.
- Image: `python:3.14-slim`, immutable image ID `sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151` (linux/arm64), already cached.
- Read-only preflight: no running containers; exact image inspect succeeded. No pull, prune, daemon repair, or VM modification.
- Each role uses one unique ephemeral container, `--pull never --network none --read-only --cpus=1 --memory=512m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 501:20`. Only role-specific source/input mounts are read-only; only that role's fresh output directory is writable. Candidate cannot mount/read the auditor oracle. These are requested limits; no claim of effective enforcement beyond the recorded container configuration.
- Candidate: `docker run --rm --name issue8466-a01-candidate-20261008 --pull never --network none --read-only --cpus=1 --memory=512m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 501:20 -v "$PWD/candidate.py:/input/candidate.py:ro" -v "$PWD/candidate_inputs.json:/input/candidate_inputs.json:ro" -v "$PWD/formal_01:/output:rw" --tmpfs /tmp:rw,noexec,nosuid,size=16m python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 python3 -B /input/candidate.py /input/candidate_inputs.json /output/RAW.json`
- Auditor (only after candidate exit 0): `docker run --rm --name issue8466-a01-auditor-20261008 --pull never --network none --read-only --cpus=1 --memory=512m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 501:20 -v "$PWD/auditor.py:/input/auditor.py:ro" -v "$PWD/candidate_inputs.json:/input/candidate_inputs.json:ro" -v "$PWD/oracle.json:/input/oracle.json:ro" -v "$PWD/formal_01/RAW.json:/input/RAW.json:ro" -v "$PWD/audit_01:/output:rw" --tmpfs /tmp:rw,noexec,nosuid,size=16m python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 python3 -B /input/auditor.py /input/candidate_inputs.json /input/RAW.json /input/oracle.json /output/AUDIT.json`

Construction tests are not formal invocations. The formal commands are one-shot and will not be retried, tuned, or replaced. Freeze SHA-256 values are in `FREEZE.json`. Recheck remote main immediately before candidate start; if it differs from the frozen SHA, stop before either formal role. Preserve any first raw output and exact exit/log evidence.
