# T6 execution report — STOP

## Outcome

**STOP_UNCLASSIFIED_ORCHESTRATOR_EXIT** — the one-shot hosted Docker workflow
failed, but the available record does not identify whether image build,
candidate startup, or orchestration stopped. No startup-gate PASS or scientific
conclusion is claimed. This allocation is not rerun.

## Frozen run and evidence

- Allocation: `MAP01-ATTACK-ONSET-STARTGATE-4223-T6-20261001-01`
- Frozen source commit: `b002ae272b168aa035b2792324775339dab92f93`
- Run: [36789533128](https://github.com/Unjuno/agent-interface/actions/runs/36789533128)
- Workflow job: `startup-gate`, failed at step 5, “Build pinned runtime and run one candidate plus independent auditor”.
- PR: [#5654](https://github.com/Unjuno/agent-interface/pull/5654)
- Uploaded Actions artifact: `map01-attack-start-gate-t6-36789533128`, artifact ID `11131141471`, declared ZIP SHA-256 `535b94ffeb7bc14d394f9f20e8baa5bc9b9f379b636c21c59db5444fd8a030f4`, 85,236,522 bytes.
- The run log confirms artifact upload completed. Repeated local downloads through `gh run download` and the artifact ZIP API did not complete in this session; local partial downloads did not match the declared size/digest and are not treated as evidence. Thus `OBSTAC_EXECUTION.json`, Docker build output, candidate output and any auditor output remain uninspected.
- The failed step’s Actions log contains only the step command and generic exit code 1, not the subprocess output. Cause is therefore unclassified; do not infer candidate failure.

## Scope and verification

OrbStack was unavailable, so this was a hosted Linux/amd64 Docker fallback, not a local run or a replicated OrbStack result. The frozen protocol allowed one candidate and zero retries; the Actions execution stopped before its result could be classified. No gameplay/onset, task-effect, physical-edge, recovery-efficacy, or map-clear claim follows.

Local package CI passed 6/6 contract tests, Python byte-compilation, `git diff --check`, workspace-index validation, and all frozen-source SHA-256 checks. These validate the harness structure only; they do not replace the unclassified Docker experiment.

## Disposition

Preserve this STOP and its immutable Actions artifact. Do not merge this PR as a verified startup result. A future successor allocation may investigate artifact retrieval/orchestrator observability and request a fresh experiment slot, without modifying this report or the historical allocation.
