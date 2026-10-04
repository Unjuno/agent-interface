# Issue #7042 T0: X11 input recovery scope

**Disposition: `INPUT_NEUTRALIZATION_ONLY`; not a process/session reset or a task-effect cure.** This is a source-based eligibility audit of one already-existing path, with its focused mocked unit suite. It does not test live X11, an application, or a formal recovery allocation.

## H / T / D / C / U

**H.** `X11RuntimeSession.recover_input()` can discharge the session's outstanding input-release obligation after an X11 readback confirms that the backend's owned inputs are up. It does not establish that a failed task completed or that its failure cause was removed.

**T.** At frozen source head `8d9940c4e0afe7895715bce77fa9f7e455e06cad`, trace `X11RuntimeSession.recover_input`, the `dispatch` refusal gate, `X11Backend.release_all`, its physical readback helpers, and the focused failure/recovery tests. The state and call order are explicit and finite, so this is an analytical screen; the existing unit suite is a regression check, not empirical GUI evidence.

**D.** Classify this operation as owner-input neutralization only. `recovery_required` clears only after a successful release result with `verified is True`, `keys_down == []`, and `buttons_down == []`. Release/readback exceptions, a down input, or an unverified result keep later dispatch refused. Successful recovery returns `task_success: None` and `replay_allowed: False`. Therefore it is **not eligible as a cure/reset arm** for a process, session, cache, or restored-state comparison without a separate failure-state and task-effect oracle.

**C.** When the failure is specifically an outstanding input owned by this backend, releasing it removes that input hazard and may allow the caller to proceed after fresh observation. That is a useful safety recovery, but does not show that an underlying application, transport, or semantic failure was cured.

**U.** No live X server, game, GUI, model, or physical input ran. Tests use mocks. Keyboard readback is deliberately restricted to keycodes tracked by this backend, consistent with the backend's rule not to release another actor's held key; it therefore cannot establish global keyboard neutrality. Mouse-button readback examines the reported button mask. Neither readback establishes application effect completion or rollback.

## State transformation

| Aspect | Observed contract |
|---|---|
| Admission | Refuses recovery when `recovery_required` is false; makes no release call. |
| Reset/discard | Emits releases for tracked keycodes/buttons, syncs the same X11 display connection, and verifies input state. No process or session is recreated. |
| Preserved | Same backend/display owner, application state, completed or partial task effects, and unresolved effect meaning. No task effect is erased or replayed. |
| Success condition | Runtime-owned tracked keys and reported buttons are empty and the release result is explicitly verified. Only then is the sticky recovery flag cleared. |
| Following action | The runtime had refused dispatch while recovery was required. This method itself grants no lease or task authority; its result says task success is unknown and replay is disallowed. |

The keyboard check calls `_physical_keys_down(tracked)`, so an empty `keys_down` means no tracked backend key remains down, not that every key on the X server is up. The distinction preserves other actors' controls and narrows the safety claim to this input owner.

Source map: release-result predicate and sticky flag, `session.py:16-21`; explicit recovery, `session.py:23-39`; dispatch gate, `session.py:49-52`; tracked-key and button readback, `backend.py:368-400`; no release of another actor's held input, `backend.py:50-53`; refusal/verified-empty/failure-readback cases, `test_partial_execution.py:33-49,102-134,264-280`.

## Reproduction and provenance

- Source commit: `8d9940c4e0afe7895715bce77fa9f7e455e06cad`.
- Integration base at validation: `96f7041fe6b3eb71127ac4eca0ed31d313c29ad2`; the three source blobs listed below were unchanged from the analytical source commit.
- Source blobs: `runtime/backends/x11_v1/session.py` `4dbd6dd219e2ec7313cd32d3e4cb154e0efcfbb1`; `runtime/backends/x11_v1/backend.py` `0b168d6e8b840f39f21cdd35cdf6d959da53fbde`; `runtime/backends/x11_v1/test_partial_execution.py` `5e5055b83c368ef55e09f89829156e4aa39ec3e6`.
- Command: `/tmp/unjuno-7042-x11-test-venv/bin/python -B -m unittest runtime.backends.x11_v1.test_partial_execution -v`.
- Runtime: CPython 3.12.10; `python-xlib==0.33`, `Pillow==10.2.0`, `six==1.17.0`; macOS arm64 host. The suite passed 12/12 with exit 0; stdout is retained in `test-partial-execution.txt`, with start/end UTC and exit code alongside it.
- This validates only mocked X11 session/release behavior. It does not validate server delivery, live readback, GUI effects, recovery rate, or benefit over YIELD.

## Separate pathway: observation-history invalidation

`ObservationHistory.clear()` is a distinct derived-state invalidation operation, not an input-neutralization operation. At `origin/main` `2f72c6474167f93a2e1a6e2b8a497a1a8a6d266a`, `runtime/guarded_x11_v1/history.py:69-72` clears the in-memory record map and decoded-image cache. It does not load or unlink artifacts, recreate the X11 connection or application, reverse task effects, or establish task success. A later lookup cannot reuse a cleared record; callers must obtain fresh observation data.

`GuardedX11Bridge.review_window()` (`runtime/guarded_x11_v1/bridge.py:304-329`) rotates the binding revision and scope, replaces the handle store, marks review required, and clears history before its read-only review. A failed handoff clears history again and keeps review required. Thus old evidence is prevented from minting authority across the handoff, while retained observation access is deliberately lost; a successful fresh review is needed to restore that review state. This may qualify only as a narrow evidence-invalidation/reset arm when the endpoint charges reacquisition cost and separately records the lost history. It is not evidence that a task failure was cured or an application effect was rolled back.

At the live `main` commit above, the source blobs are `history.py` `7b515384ce1fd4a6c532542a4cb53bc67e304bb3`, `bridge.py` `42466a34b631201fe52f6d0b6c851b7649eb3b25`, and `test_history.py` `639b6437b65032929e5a2f4f35404a8417f16a42`; all three blobs are byte-identical at this report branch's `HEAD` (`a5103717940213b69d74526fc8837f917312c6ae`). The focused command `/tmp/unjuno-7042-x11-test-venv/bin/python -B -m unittest runtime.guarded_x11_v1.test_history -v` passed 5/5 (exit 0), with output and UTC bounds in `test-history.txt`, `test-history-start-utc.txt`, and `test-history-end-utc.txt`. This is a mocked unit check of local history/cache behavior only, not a live X11 or application recovery experiment.
