# Issue #8473 T0 A01 preregistration

Allocation: SCOPED-NOGOOD-GUI-PLAN-8473-T0-A01-20261008  
Issue: https://github.com/Unjuno/agent-interface/issues/8473  
Base: main@11e0bf72e6199d2a72fb002f1949d9e5082d6bdc  
Package: research/analysis/scoped_nogood_gui_plan_8473_t0_a01_20261008/

## H / T / D / C / U

- **H:** A verified lower-level infeasibility scoped to an operation, target, surface, evidence generation, and expiry can reduce duplicate equivalent infeasibility queries without losing feasible alternatives after local recovery, evidence-generation change, or expiry. Global action blacklisting is expected to lose at least one feasible alternative. Timeout and unmodeled/unknown outcomes must never create a no-good.
- **T:** Exhaustively execute seven authored finite scenarios under NO_FEEDBACK, GLOBAL_BLACKLIST, and SCOPED_NOGOOD: occluded target with rearrangement alternative; unavailable focus with refocus alternative; genuinely no alternative; transient blocker cleared by a new evidence generation; a same-generation constraint that expires; unmodeled/UNKNOWN then recheck; TIMEOUT then recheck. Candidate sees only candidate_inputs.json; oracle.json is auditor-only. Candidate runs once; independent raw-only auditor runs once only after candidate exit 0. Five frozen output corruptions challenge blocker omission, scope globalization, stale-generation reuse, timeout-to-infeasible relabeling, and alternative deletion. No retries.
- **D:** PASS_METHOD_SCOPED only if all 21 scenario-policy runs are independently audited; the scoped policy reduces duplicate same-state infeasibility queries on both recovery cases, retains every oracle-feasible alternative, does not prune after generation change or expiry, treats UNKNOWN/TIMEOUT as recheckable non-infeasibility, returns no effect for the no-alternative case, and all five corruptions are rejected. Any feasible-path pruning by SCOPED_NOGOOD is FAIL_UNSOUND_PRUNING; missing/incomplete grounding is HOLD; absence of duplicate-query reduction is NO_RESIDUAL.
- **C:** Stateless replanning may be sufficient; a global blacklist is a diagnostic over-pruning control, not a serious candidate policy. The fixture assumes a complete exact feasibility oracle and a deterministic proposal sequence.
- **U:** Synthetic symbolic states do not establish that screenshot-derived GUI reasons are sound or complete, that query reduction lowers model tokens or wall-clock time, or that a deployed planner should persist constraints. No action, GUI, human, safety, or product claim follows.

## Freeze and isolation

Read-only OrbStack preflight at 2026-10-08T03:45Z: Docker context orbstack, Engine 29.4.0, Linux/arm64, cgroup v2; pinned python:3.14-slim image already cached as python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151. docker ps returned no running containers. No pull, prune, daemon repair, or VM change. Requested role limits: one CPU, 512 MiB, 64 pids, network disabled, read-only rootfs, dropped capabilities, no-new-privileges; only explicit output directory is writable. These are requested Docker settings; effective resource enforcement is not claimed.

The source/input/oracle are mounted read-only. Candidate cannot access the oracle. Candidate and auditor use separate fresh containers and output directories. Formal candidate/auditor invocations are one-shot; a nonzero exit is retained as STOP/FAIL and is not retried or tuned.

Candidate command (run from this package directory):

~~~
docker run --rm --name issue8473-a01-candidate-20261008 --pull never --network none --read-only --cpus=1 --memory=512m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 501:20 -v "$PWD/candidate.py:/input/candidate.py:ro" -v "$PWD/candidate_inputs.json:/input/candidate_inputs.json:ro" -v "$PWD/formal_01:/output:rw" --tmpfs /tmp:rw,noexec,nosuid,size=16m python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 python3 -B /input/candidate.py /input/candidate_inputs.json /output/RAW.json
~~~

Only after candidate exit 0, auditor command:

~~~
docker run --rm --name issue8473-a01-auditor-20261008 --pull never --network none --read-only --cpus=1 --memory=512m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 501:20 -v "$PWD/auditor.py:/input/auditor.py:ro" -v "$PWD/candidate_inputs.json:/input/candidate_inputs.json:ro" -v "$PWD/oracle.json:/input/oracle.json:ro" -v "$PWD/formal_01/RAW.json:/input/RAW.json:ro" -v "$PWD/audit_01:/output:rw" --tmpfs /tmp:rw,noexec,nosuid,size=16m python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 python3 -B /input/auditor.py /input/candidate_inputs.json /input/RAW.json /input/oracle.json /output/AUDIT.json
~~~

Pre-freeze construction tests are non-formal and may be repeated. The formal invocations may not.
