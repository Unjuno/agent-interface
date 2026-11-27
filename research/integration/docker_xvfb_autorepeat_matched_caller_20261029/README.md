# Matched global auto-repeat control through the standard MCP caller — 2026-10-29

## Preregistered schedule

A-B-B-A: repeat ON, OFF, OFF, ON. All four arms used a fresh pinned Linux/amd64 Docker container and private Xvfb `:88`; the same current-main blocked-sync standard MCP test and exact four runtime/test source hashes; 4,000 ms pidfd stop; 8,000 ms delayed B XTEST request; prestarted cancellation supervisor; zero withheld ack; and the test-only 12 s cancellation transaction. A persistent X client held the requested mode and sampled mode/A state about every 5 ms. No arm was retried.

| Arm | Repeat mode samples | Old task count (expected 1) | Extra A presses after cancel | Oracle |
|---|---:|---:|---|---|
| A1 | 1,111, all 1 | 4 | 3 at +3947.438, +3989.212, +4028.903 ms | FAIL |
| B1 | 1,046, all 0 | 1 | 0 | PASS |
| B2 | 1,056, all 0 | 1 | 0 | PASS |
| A2 | 1,063, all 1 | 4 | 3 at +3946.836, +3988.636, +4028.353 ms | FAIL |

For both ON arms, the nearest mode samples to every extra A press read 1, within 5.879 ms. Consecutive repeat intervals were about 41.8 ms and 39.7 ms. All arms had an approximately 4 s observation gap while Xvfb was stopped; mode was sampled before and after the pause. Full raw reports, independent monitor streams, stdout, exit codes, images, conditions and SHA-256 manifests are preserved in the local family packet `private-packets/docker_xvfb_autorepeat_matched_caller_20261029/`.

## Recovery and API outcome

Across all arms the exact owner retired, disconnect was observed, supervisor release readback was `readback_verified`, independent release and horizon readbacks were all-up, delayed B was absent at the ~8.5 s horizon, and a distinct fresh-C task oracle passed. The canceled old API call remained `release_confirmed=false`, cleanup `UNKNOWN`, `task_success=null`, replay denied, terminal `runtime_failed` in every arm. Docker and unittest exited 0 in all four arms; the old-task oracle results above determine whether the task effects were correct.

## Interpretation

The repeated A-B-B-A result supports global Xvfb autorepeat as a contributor to duplicate A effects under this exact synthetic caller schedule. It is diagnostic evidence at n=2 per condition, not a reliability estimate and not an exact reconstruction of historical R02, whose complete raw was overwritten. The global keyboard setting is server-wide; the isolated-Xvfb control does not authorize making repeat suppression a default behavior on a shared desktop. A production design needs explicit exclusive-ownership policy, restoration after verified neutral state, and conservative UNKNOWN handling.

This does not establish native Win32/WSLc transfer, MAP01 completion, broad reliability, production readiness, or efficiency improvement.
