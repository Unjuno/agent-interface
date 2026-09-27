# Issue #4520 — one-shot broker exit status

## H / T / D / C / U

**H.** The current one-shot broker converts a successful child exit `0` to broker exit `1` because `broker.get("returncode") or 1` treats zero as missing. Exact nonzero child codes should propagate unchanged; timeout and executable-unavailable receipts must remain nonzero and typed.

**T.** On current `main` commit `e786135bf5576f308c7d0185cfb484b9970bf6de`, the baseline broker/test Git blobs exactly matched the frozen Issue values: broker `f307daafdfd36d1ab4faf39bb36c36350e6e67e4`, test `e645ae575cd6fdae02556df9facc9919739584f3`. Added four deterministic mocked-child regressions for child exits 0 and 23, timeout, and missing executable. No real model/provider/GUI/input call was made. The code change is limited to distinguishing `None` from integer zero in the existing one-shot return mapping.

**D. `PASS_HOST_BROKER_EXIT_PROPAGATION_FIX` (scoped).** Before the fix, the isolated container test run reproduced the issue: 7/8 passed and only child-exit-zero failed (`expected 0`, observed `1`). After the fix, all four new regression cases pass: child `0` returns `0`, child `23` returns `23`, and timeout/unavailable return nonzero with their existing typed stop reasons. Broker receipts retain the exact child code or `null`, response contents match mocked stdout (empty on failure), and authority remains false.

**C.** This validates the local process/broker contract only. The subprocess is mocked; no Codex executable, model service, or host/container IPC endpoint was invoked. Historical #3926/#4485 evidence and dispositions are unchanged.

**U.** No live endpoint/schema compatibility, Docker Desktop/amd64 equivalence, GUI/task correctness, or product claim follows.

## Source and execution

- Intake base: `e786135bf5576f308c7d0185cfb484b9970bf6de`.
- Delivery branch `fix/issue-4520-zero-exit-20260927` was rebased onto current main `c6ad3e83db1ee835859ad9724c9e1747cb7fd48d`; GitHub comparison found no broker/test/evidence-path changes across the intervening 20 commits.
- Frozen broker/test baseline blobs: `f307daafdfd36d1ab4faf39bb36c36350e6e67e4` / `e645ae575cd6fdae02556df9facc9919739584f3` (both rechecked exact at intake).
- Local container: `python:3.12-slim-bookworm`, image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, Linux/arm64, Python 3.12.14; network disabled, source bind-mounted read-only, root read-only, bounded `/tmp` tmpfs, 1 CPU, 512 MiB, 64 PIDs. This local machine has no cached linux/amd64 variant of the required image.
- Exact applicable workflow command (host Python 3.14.5): `python3 -m unittest runtime.test_docker_host_model_bridge_v1 runtime.test_host_model_ipc_broker_v1 research.live_control.issue_3311_host_ipc_v1.test_audit_orbstack_v1_transport research.live_control.issue_3311_host_ipc_v1.test_orbstack_v1_transport.OrbStackV1TransportTest.test_broker_is_reaped_when_image_inspect_fails research.live_control.issue_3311_host_ipc_v1.test_orbstack_v1_transport.OrbStackV1TransportTest.test_broker_is_reaped_when_image_inspect_times_out -v` — **27 passed**.
- Direct affected suite in OrbStack (Python 3.12 image above): `python -m unittest runtime.test_docker_host_model_bridge_v1 runtime.test_host_model_ipc_broker_v1 -v` — **10 passed**.
- `git diff --check` uses `core.whitespace=cr-at-eol` for the two pre-existing mixed-line-ending Python files; no whitespace defects remain in the patch.

## Preserved infrastructure observations

The first read-only-root container attempt lacked writable `/tmp`, so its four new cases stopped before reaching broker code. Re-running with the bounded `/tmp` tmpfs produced the pre-fix 7/8 result above. A later attempt to run all 27 workflow tests in the minimal Python container reached the unrelated retained-evidence tests but 17 errored because that image has no `git` executable; those same 27 workflow tests passed on the local host. The directly affected 10 tests passed in the container. These are environment boundaries, not scientific failures.
