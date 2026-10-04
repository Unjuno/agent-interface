# Native-to-caller integration decision

Evidence handoff for #57, based on completed Q01/J01/B01/M01/N01 allocations. This is a reduction of saved results, not a new experiment or a source adoption vote. Original results and first failures remain unchanged.

| Evidence | What was executed | Integration implication |
| --- | --- | --- |
| Q01, `../caller_current_coupling_57_4d74_20261004/` | Full pending PR7234 caller plus named main core, 31 ordinary test methods passed in WSLc | Offline composition is supported; native authority/effect/total-cost qualification remains missing. |
| J01, `../caller_native_join_57_4d74_20261004/` | Saved actual P01 native receipt through unchanged pending caller callbacks | Full receipt is rejected by the legacy status-only execution decision. Explicit conversion is required; this alone is not a contract bug. |
| B01, `../motor_native_join_57_4d74_20261004/` | Existing MotorState native-result conversion on saved receipt and controlled copies | Existing schema bridge should be reused for state representation. It preserves OS_UNCONFIRMED and does not confer current-context authority or caller compatibility. |
| M01, `../caller_native_state_mapping_57_4d74_20261004/` | Three authored noncompleted caller decisions | Typed incomplete outcomes retain uncertainty and authority distinctions. These fixtures are not an automatic native converter or actual failure qualification. |
| N01, `../native_noinput_units_57_4d74_20261004/` | Fresh native private Xvfb wait_update/release_all program | Native completed_ops has two entries while tracked ordinary emissions are zero. Operation completion and dispatched input need distinct declared units. |

## Decision and next meaningful rung

HOLD production adoption. Do not pass the full native receipt directly to the narrow caller decision, infer input dispatch from len(completed_ops), or promote owned tracked release to global physical neutrality. Preserve the complete original receipt and its hash beside any derived decision; a hash is custody, not semantic validation.

The next useful integration experiment requires an explicit native-to-caller converter with declared count units, typed native status/recovery handling, retained non-input prefix evidence, and current authority checks supplied by the established owner. Test actual completed, pre-input refused, partial execution and release-unverified outcomes, including useful task effect and bounded recovery. Authored manual mappings cannot substitute for those actual cases. Existing #2437 owns native cleanup/recovery; pending PR7182/7234 retain their caller source owners and approval/application gates. This handoff grants neither a consumed allocation retry nor ownership transfer.

Stop additional manual-mapping/native count microvariants: the boundary is already demonstrated. The full #57 same-task/same-model cold/warm and all-attempt cost/effect evaluation, second-domain transfer, and ROADMAP remain incomplete. No causal speedup, GPU benefit, or usable product claim follows from these archives.

## Custody and current-state scope

`CUSTODY.json` records a fresh literal Git-byte audit of all 88 manifested members in the five archives, with zero byte/hash errors. It also records no selected core/X11/MotorState/caller source changes between native pin d744d19de5b4a44f5b6898eeb25516bbaf481 and fetched main 6dee2bff223c7e9643949d2a8ef3acf7e9b007da. This does not turn the earlier executions into a current-main composed execution certificate. No saved actor or auditor was imported or replayed by this custody check.

GitHub comment/PR creation remains subject to a secondary rate limit, with an explicitly recorded minimum retry time of 2026-10-03 22:35:38 UTC. These experiments had local prospective freezes, not successful GitHub preregistration. Evidence branches were pushed; no PR or main delivery is claimed until those operations succeed. Owned unmerged branches must remain available.

Intake command errors are retained in the session: an initially missing sparse-worktree README, wrong root CURRENT_GOAL path, and ambiguous short Git object `7234`; corrected reads used Git objects, docs/CURRENT_GOAL.md, and exact source pins. None caused an experiment retry or result rewrite.
