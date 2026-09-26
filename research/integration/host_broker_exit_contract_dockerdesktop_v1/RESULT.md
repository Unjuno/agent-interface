# Docker Desktop host-broker exit/receipt contract — result

Date: 2026-09-26 JST. Parent question: [Issue #3924](https://github.com/Unjuno/agent-interface/issues/3924). Allocation tracking: [Issue #3926](https://github.com/Unjuno/agent-interface/issues/3926).

## Disposition

- **Scientific disposition:** `FAIL_ZERO_EXIT_PROPAGATION` (predicted deterministic contract defect reproduced).
- **Raw-case audit disposition:** `AUDIT_PASS_RAW_CASES_HOLD_HOST_DOCKER_EXIT_UNOBSERVED`, errors `[]`.
- **Overall formal/reporting state:** `HOLD_HOST_DOCKER_EXIT_RECEIPT`. The formal wrapper's Docker CLI exit receipt is unobserved; it is not inferred from the container's inspect exit. This is not an overall formal PASS.
- **Production source:** unchanged.

## Frozen environment and provenance

Formal allocation 02 used Docker Desktop context `desktop-linux`, Engine `28.5.1` Linux/x86_64, and `python:3.12-slim` image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (`linux/amd64`). The frozen base snapshot is `3e1d4524b80ec230d28efe9a5b9865681cc7df27`; later main commits were admitted only while that base remained an ancestor, both target blobs remained equal, and the allocation path remained untouched. Broker Git blob `f307daafdfd36d1ab4faf39bb36c36350e6e67e4`; existing test Git blob `e645ae575cd6fdae02556df9facc9919739584f3`.

No real Codex executable, credential, model/provider request, GUI, game, or user input was used. The formal container had network `none`, read-only rootfs and source mounts, 1 CPU, 256 MiB, 64 PIDs, all capabilities dropped, and no-new-privileges. Its exact raw request/receipt/process evidence and byte inventory are retained under `raw/`.

## Allocation history

1. `dockerdesktop-20260926-01`: `STOP_DOCKER_MOUNT_FLAG_SYNTAX`. Docker rejected the invalid `rw` field before creating a container; formal cases run = 0. The STOP is preserved at `formal/dockerdesktop-20260926-01/STOP.md`.
2. `dockerdesktop-20260926-02`: one formal suite invocation. All seven tests completed; summary reports tests=7, failures=0, errors=0; Docker inspect reports the formal container exited 0 and was not OOM-killed. PowerShell then terminated on unittest progress written to native stderr before it captured the Docker CLI exit code. Wrapper exit 1 is observed; Docker CLI exit is explicitly `null`/unobserved. See `WRAPPER_STOP.md`, `formal_run.json`, inspect, and Docker log.
3. Frozen independent audit 01 recomputed all seven case verdicts, with one error: `formal container did not exit cleanly`. This is the missing host Docker CLI exit receipt; it did not report a raw case, frozen-source, or isolation mismatch.
4. Posthoc audit V2 allocation 01: `STOP_AUDITOR_UNRECOGNIZED_ARGUMENT` (argparse exit 2 before entering audit logic). Preserved under `posthoc_audit_v2/`; not rerun there.
5. Posthoc audit V2B: separately frozen read-only audit, one invocation, Docker and container exit 0. It independently verified all seven raw cases, byte inventory, source identities and formal container constraints; result errors are empty and the explicit host-exit HOLD remains. It does not upgrade the overall formal status.

## Formal case results

| Case | Observed evidence | Classification |
|---|---|---|
| Exit 0 | Child and receipt return 0; broker process returns 1 | `FAIL_ZERO_EXIT_PROPAGATION` |
| Exit 23 | Receipt and broker process return 23 | `PASS_NONZERO_PROPAGATION` |
| Timeout | Typed `TimeoutExpired` / `HOST_BROKER_SUBPROCESS_TIMEOUT`; broker nonzero | `PASS_TYPED_TIMEOUT` |
| Unavailable executable | Typed `FileNotFoundError` / `HOST_BROKER_EXECUTABLE_UNAVAILABLE`; broker nonzero | `PASS_TYPED_UNAVAILABLE` |
| Malformed JSON | Nonzero, no receipt or response, `JSONDecodeError` | `PASS_MALFORMED_FAIL_CLOSED` |
| No request | Remained alive through 200 ms observation; no IPC artifacts; harness then terminated it (`-15`) | `PASS_BOUNDED_NO_REQUEST_IDLE` |
| Two queued requests in `--once` | Only request A received one response/receipt; request B remained queued; broker returned 1 for child exit 0 | `PASS_ONE_SHOT_CARDINALITY` |

## Interpretation and limits

The defect is localized to `return broker.get("returncode") or 1`: a successful child return of zero is converted to broker exit 1. This is a deterministic fake-process contract result for the pinned source under one Docker Desktop Linux/amd64 configuration. It does not establish real model utility, GUI/task success, arbitrary subprocess safety, or OrbStack equivalence. Because the host wrapper did not retain its Docker CLI exit receipt, keep the overall evidence state at HOLD even though the formal container's own inspect exit is 0 and the independent read-only raw audit found no case-integrity errors.

The next engineering step, if pursued, is a separately reviewed broker fix and regression test. This research bundle itself does not modify runtime code.
