# Child authority and actual cleanup after a stopped Xvfb resumes

This WSLc pair follows the [child-authority guarded cancellation composition](../wslc_explicit_auth_guarded_cancel_20261101/README.md). An actual spawned guarded owner sent `a` to a separate target; the target recorded the press and an independent X client observed the key down. A test hook paused the owner after the press, the private server was stopped, and real cancellation was started. After the prestarted cleanup worker entered, the harness resumed Xvfb 300 ms later, within the cancellation transaction budget. The parent held an invalid authority at owner startup; the owner and supervisor received the private authority through the draft's explicit child-scoped option.

| Observation | Correct cleanup authority | Deliberately wrong cleanup authority |
| --- | --- | --- |
| Old owner cancellation | owner retired; old cleanup `UNKNOWN`, no replay | same |
| Cleanup stage | XRes disconnection observed; release request and supervisor readback verified | XRes query failed; release unconfirmed |
| Independent X key readback before fixture cleanup | `a` up | `a` down |
| Old target before fixture cleanup | recorded `a` press and release | recorded `a` press only |
| Fixture release needed before fresh task | no | yes |
| Fresh guarded task | separate target received `a`; release verified; final input neutral | same, after fixture release |

The wrong-authority arm changes `XAUTHORITY` inside a test wrapper around the cleanup worker; the owner itself uses the correct authority in both arms. It returned `xres_query_failed`; the archived outer receipt does not retain the worker's detailed authentication error, so this is a controlled negative outcome rather than independent proof of the exact failure cause. The correct arm shows an actual release request, supervisor readback, independent key-up and target release for this case. The cancellation result still correctly preserves product-level `release_confirmed=false`, `cleanup_status=UNKNOWN` and `replay_allowed=false`: a single readback does not prove that no old queued request can later arrive or that the old task succeeded.

Both fresh fixed-order allocations used main `e5925b6bd99fd4ff3f8e0bda5ed4d7cc02d92c4d`; the modified owner, supervisor and private-display module match draft [#10088](https://github.com/Unjuno/agent-interface/pull/10088) `926ba07214b5ab53ff38f66af5c0947606850118`. Other source comes from the earlier [#10074](https://github.com/Unjuno/agent-interface/pull/10074) snapshot; the mixed tree is retained and is not claimed as one commit. Pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25` ran with one CPU, 1 GiB memory limit, no network and no pull. WSLc reported swap was not limited.

[raw.zip](raw.zip), SHA-256 `7bc1daed5c06504420c35e371f04eaf2148576a0b2a44c46471df83555121143`, retains frozen source, conditions, events, receipts and outputs; ephemeral authority files are excluded and the archive was checked for their key bytes. The audit checks frozen hashes, custody and event ordering, the independent key states, target events, fresh task and process exits. The owner pause and server stop were injected, the two conditions ran once in fixed order, and no actual delayed server request was intentionally queued. This is not evidence of general finite recovery, production MCP integration, a hard deadline, MAP01 completion or a reliability rate.
