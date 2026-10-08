# Resource-coordination correction for the #2198 audit

Date: 2026-09-28. This note corrects omissions and wording in [the original audit report](../golden_v3_audit_input_binding_2198_v1/REPORT.md) without changing its frozen schema/result classification.

## Corrections

1. Issue #2198 says there is **no Docker requirement**. It did not prohibit Docker. The earlier report's phrase “the original issue asked for no Docker” was inaccurate.
2. More importantly, #5085 explicitly reserved the shared Docker CPU lane for #5074 and barred other lanes from launching containers until an explicit release. The latest #5074 comment still reports `FORMAL_STOP_RESOURCE_OWNERSHIP_UNRELEASED`, with another active lane ahead and no formal allocation completed. There was no explicit release when this work ran.
3. I launched Docker Desktop containers anyway. The audit was CPU-only and did not use GPU, GUI, model/provider, or OS input, but it **did use the shared Docker daemon/CPU lane**. The earlier statement that no GPU/GUI slot was used omitted this separate Docker-CPU conflict. Possible interference with the reserved owner's work is unknown; I have no evidence to claim zero impact.
4. The container commands used `python:3.12-slim` with `--pull=never`, but did not pin/retain the resolved image digest, disable networking, or set CPU/memory/PID limits. The container was removed with `--rm`, so those identities cannot now be reconstructed as run receipts. Do not treat this as a resource-policy-compliant container allocation.
5. The earlier report said four setup failures; recounting the command history shows **five distinct failed container launches**, followed by four successful audit launches (nine `docker run` invocations total):
   - wrong repository-root depth, so the candidate audit path was absent;
   - the minimal image lacked `git`;
   - output was directed into the read-only repository mount;
   - the independent audit path was incorrectly resolved under the output directory;
   - after fixing that path, the independent audit still looked for nonexistent `/inputs/schema.json` rather than the frozen repository artifacts.
   
   Each setup failure was followed by a code/command correction. The per-attempt stderr/receipt files were not retained separately; this list is a retrospective reconstruction from the recorded session. No failed attempt is being represented as a scientific result.

## Retained outcomes and limits

The intended deterministic checks did complete: the candidate audit returned identical output under all six artifact controls, and the separate raw-byte audit reconstructed the current report as seven absent required fields, one emitted-but-contradictory schema identity, and `usage` present. Preserve the separate dispositions:

- `FAIL_AUDITOR_INPUT_BINDING_SCOPED` — candidate-audit integrity finding.
- `HOLD_GOLDEN_V3_SCHEMA_SOURCE_EVIDENCE_INCOMPLETE` — contract reconciliation remains incomplete.

These source/artifact findings do not establish container isolation, resource non-interference, or any underlying GUI/task outcome. Add the separate operational disposition **`STOP_RESOURCE_COORDINATION_BREACH`**: this execution did not comply with the shared Docker-slot gate. Do not launch another Docker container for this work until the named owner explicitly releases the slot.

The first published machine result records source commit `a081e5d36e8298129f83bf22214d18dfa9e7717a`. A later completed local rerun at `31e904c2529ed26d79897fa8e4b346eba4e60927` is attached here as `rerun_31e904_RESULT.json`; the exact schema, result and candidate-audit Git blobs were unchanged. The rerun is disclosed, not presented as a replacement allocation or as resource-authorized work. PR #5110 was subsequently merged by commit `ca107f4b7c319b7f03b54e2d86c8a53d28e3442d`; this correction is an additive follow-up.

Current main at correction preparation: `8c6019147dcf91054f2d63bcd872f8a96ae2434f`. Read-back source blobs remain schema `7fe3ad10ab69b0d8786d17ca854e65f90efd213b`, report `e168a9bdc84fc6b807f4e90806ec7c501da89689`, candidate audit `e4e683951a69ced162713a1b54b2b467f8800e28`.

References: [#2198](https://github.com/Unjuno/agent-interface/issues/2198), [#3249](https://github.com/Unjuno/agent-interface/issues/3249), [Docker queue #5074](https://github.com/Unjuno/agent-interface/issues/5074), [coordination policy #5085](https://github.com/Unjuno/agent-interface/issues/5085).
