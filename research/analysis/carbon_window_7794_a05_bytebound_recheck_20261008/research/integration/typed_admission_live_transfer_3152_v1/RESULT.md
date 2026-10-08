# Retained-case completeness audit — Issue #3152

Disposition: **HOLD_LIVE_EVIDENCE_INCOMPLETE**. This is a post-hoc audit of one existing model-facing case, not a #3152 formal allocation.

## H/T/D/C/U

- **H:** retained case `adaptive-semantic-repair-live-02/case-02-model` contains the typed/scalar comparison fields needed for a #3152 held-out row.
- **T:** one Docker audit parsed the immutable report and action/release records. No model call, GUI execution, task rerun, or policy replay occurred.
- **D:** required evidence role, measured observation cost, downstream reserve, typed decision, and scalar decision were all absent. Final disposition was present. Therefore retain HOLD, not PASS/FAIL. Formal #3152 allocation count remains 0.
- **C:** this historical case targeted adaptive semantic repair, not fidelity admission. Its useful model/task evidence does not imply it captured the later comparison fields.
- **U:** one existing case cannot establish held-out policy behavior, model-quality gain, or generality.

## Reproduced measurements

- source case report SHA-256: `19e653441b9d76d730df2a265ad2b1d38682827c044c29241b9b8ba218f9a765`
- model calls: 2; input tokens: 18,696; visible images: 2
- adaptive model wait: 7,197.203241 ms; capture-to-caller return: 7,871.585262 ms
- action programs completed: 4/4; verified empty releases: all
- final independent form value: `t000217`
- missing: required role, measured observation cost, downstream reserve, typed policy decision, scalar policy decision

## Provenance and command

Base/current-main commit at audit: `cd2b5e9ae174737c30ca94ac60ef943a77c2b159`.
Image: `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, Python 3.12.14, Linux/amd64. The runtime command used `wsl.exe -d Ubuntu -- docker run` because Windows Docker client could not see WSL ext4 paths directly. Source and case were read-only; network was disabled; output was a separate writable path; container ran as WSL UID/GID 1002.

Exact command:

```sh
docker run --rm --name typed-admission-3152-retained-case-audit-v1c \
  --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 32 --memory 256m --cpus 1 \
  --user 1002:1002 \
  --mount type=bind,source=/home/taka/agent-interface-3152-sparse/research/integration/typed_admission_live_transfer_3152_v1,target=/src,readonly \
  --mount type=bind,source=/home/taka/agent-interface-3152-sparse/research/live_control/results/adaptive-semantic-repair-live-02/case-02-model,target=/case,readonly \
  --mount type=bind,source=/home/taka/agent-interface-3152-sparse/research/integration/typed_admission_live_transfer_3152_v1/raw,target=/out \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=16777216 --workdir /src \
  --entrypoint python python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 -B /src/audit_case.py /case /out/AUDIT.json
```

The initial attempt omitted `--user 1002:1002` and the container correctly refused to write into the WSL-owned 0755 output directory. It did not modify source or formal data. The corrected audit first passed, then the auditor was strengthened to recursively inspect nested report keys and rerun once as v1c; the output and decision were unchanged. An independently structured raw-only assertion rechecked the five missing fields, completed actions, empty releases, zero formal allocations, and the retained report hash.

- auditor SHA-256: `3ee001825ca85a1bdb644ccbac9c4f9f9f208e59570e554a637ffeba1b9b960f`
- audit output SHA-256: `9df7070c61d95bc3058047bfccd26c542f469b1961d63094d634bca36cf9f16e`
- audit status: `HOLD_LIVE_EVIDENCE_INCOMPLETE`; independent raw-only reconstruction: PASS

## Limits / next evidence

This result only prevents accidental reuse of the historical case as a complete #3152 comparison. It does not exercise the current-main broker gap documented separately in PR #4756 and does not replace that work. A formal #3152 run still needs a frozen held-out set with observed role coverage, per-variant observation cost, downstream reserve, both policy decisions, permitted escalation, model output, and independent final task scorer. Keep Issue #3152 open.
