# T1 A06 terminal method STOP — future episode leakage in prompt (2026-10-08)

**Disposition: `FAIL_METHOD_PROMPT_LEAKAGE`; no cadence result.** Candidate ran once and completed 390 calls with all runner/tag identity gates recorded. The frozen transition auditor ran once and returned `FAIL_METHOD` with 12 errors. All 12 were premature conflict claims at prefix 4: the future ep05 observation `published` / `src-05` was not yet in the episode evidence. This occurred in per-episode and batch-2 arms for each of three seeds.

Inspection of the frozen consolidation template confirms the method defect: it directly names `src-04`, `src-05`, and the future conflict contents before the model receives ep05. The model could therefore emit a conflict before the evidence was visible. A06 answer scores are not treated as valid schedule findings. The model call allocation is exhausted; no retry, prompt edit, rescore, or pooling is permitted. A future allocation must remove episode-specific future facts from prompts and use generic evidence-bounded rules.

- Candidate: exit 0, 390 calls, one invocation. Auditor: exit 0, one invocation, status/decision `FAIL_METHOD`, 12 errors. Retries: 0.
- Raw: 1925599 bytes, SHA-256 `6ae1b0539f4e246e4d787ee5d8f1531f1a7eeaf121d8dae8fa61f7ea38bffe6a`.
- Auditor JSON SHA-256 `f066c2f854f8e9b80d0295fe91b35ff3160fe91f5ab3a3a2a9e595d4b932a7e8`.

Preserve this result as method-failure evidence. Do not resume or repair A06.
