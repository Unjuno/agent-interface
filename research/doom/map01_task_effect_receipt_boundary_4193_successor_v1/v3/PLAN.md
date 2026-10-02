# #4193 retained-source receipt/schema compatibility successor v3

## Lineage and scope

This is an additive, read-only schema-compatibility reanalysis of the already retained #4193 source. It does not modify, replace, or reinterpret the immutable #4193 first result, nor the synthetic v1/v2 studies in the parent directory. No live run, container run, resource allocation, retry, or new experimental action occurred.

Intake main: `8265c1a19cbba7ab0f5316f27bdb59509269399d` (2026-09-30). Source path: `research/doom/map01_v12_attack_task_effect_live_v1/RAW_USED.json.xz`; compressed bytes 7,392; SHA-256 `0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740`. The original #4193 freeze, plan, outcome, and source remain authoritative for its first allocation.

## H / T / D / C / U

**H.** For each of the three fixed ATTACK sessions, retained physical DOWN and UP brackets can be joined to one actuation using native adapter edge identity plus owner, intent, and key. The same retained records do not establish a positive independent task effect: none of their scorer streams contains a kill-count increase or a false-to-true map-exit transition.

**T.** Read the immutable XZ JSON object. For each attack, locate native `input_admission` and `input_release_transition` events and their nested `physical_key_measurement.bracket` and `adapter_edge` objects. Require a confirmed down/up, nonempty native press/release IDs, equal actuation ID, owner ID, intent token, and key across both edges and brackets. Check scorer sample timestamps are strictly increasing *within each session only*. Compute positive endpoints from observed scorer samples: a kill-count increase relative to the first sample, or a map-exit transition from false to true. Preserve the array position as the local sample index; a derived event locator is `(session key, sample index, sample_ns, endpoint kind)`, and is emitted only when an endpoint exists.

**D.** The scoped physical join is supported only if all three attack sessions satisfy the exact native bracket/adapter checks and all six scorer streams pass schema/order checks. Task effect is supported only if at least one attack stream has a positive endpoint and no matched no-input stream does. The retained first result is `HOLD_NO_POSITIVE_SCORER_EVENT` when physical joins pass but attack positive endpoints are 0/3. Any source hash, schema, or identity mismatch is `FAIL_SOURCE_COMPATIBILITY`; unavailable/corrupt source is STOP. This classification is a static reanalysis, not a fresh intervention or replication.

**C.** Session keys bind the fixed one-actuation schedule in the original corpus; they are not general plan/actuation IDs. `sample_ns` is treated as same-process monotonic and compared only inside its own session, consistent with the predecessor plan. Event kinds are derived from scorer transitions, not claimed as producer-emitted IDs. No cross-session time ordering, application consumption, causal task effect, or recovery policy is inferred.

**U.** No new live MAP01 run, Docker/OrbStack use, GPU/provider/model, external action, allocation, task, kill, exit, recovery, product, latency, or general efficacy claim. A future multi-actuation/recovery study still needs an explicitly frozen plan-to-actuation relation and a live resource assignment.

## Reproduction

Run `python -S -B runner.py RAW_USED.json.xz RESULT.json`, then independently run `python -S -B audit.py RAW_USED.json.xz RESULT.json`. Both use only the Python standard library. The auditor reopens the frozen source and reconstructs the counts/joins/endpoints without importing the runner. The expected source file can be downloaded from the linked #4193 path at the intake revision, then checked against the SHA above. No output from these scripts changes the original #4193 allocation result.
