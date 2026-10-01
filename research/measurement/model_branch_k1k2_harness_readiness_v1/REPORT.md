# Matched K1/K2 model-branch harness readiness — first outcome

Decision: `HOLD_MODEL_RUNTIME_UNAVAILABLE`.

The static matched-model harness is ready and source-frozen:

- K1 and K2 prompt UTF-8 payloads are both 681 bytes;
- they differ at exactly one byte, offset250, ASCII `1` -> `2` in `MAX_BRANCHES`;
- K1/K2 prompt SHA-256 values are `1b6609658b948d8a7904a81d8346e0011059b6c33cd1aaabcfd499eae3eed292` and `aae1e50261ca591df2e42bbb13d3fc952bf06c2568fb595f095707f1f5a640a9`;
- each arm is exactly one model generation; K2 branch2 may not come from a second call;
- strict parser accepts exact no-authority branch objects and rejects extra branches/authority fields;
- retained JSONL extractor requires one completed agent message and one `turn.completed` provider usage record.

Runtime preflight found Python3.13.5 and Node v22.16.0 at `/opt/nvm/versions/node/v22.16.0/bin/node`, but no `codex` executable and no approved Codex CLI JS at the frozen candidate paths. No download/install/reconfiguration was attempted. Model/provider/network/GUI/task-input actions all remain0.

Therefore the actual K1/K2 model-cost allocation remains blocked in this container. The correct next action is not a mock model and not a second generation. Run the already-frozen harness only in an environment that already exposes the approved CLI/runtime, then compare the measured same-generation incremental K2 wall against #1207's conservative7.721722 ms budget while retaining provider usage separately.

Independent audit PASS; copied-result corruptions5/5 reject; source rehash exact; formal preflight invocation1/reruns0.
