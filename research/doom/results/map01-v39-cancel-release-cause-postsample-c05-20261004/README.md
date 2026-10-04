# Post-sample cancellation publication check (C05)

## H / Hypothesis

When cancellation becomes visible after the owner has sampled its cancel cause but before fake `KeyRelease`, ExecutorV12 should classify the release as `cancelled`, publish a verified empty-state `input_released` receipt, and publish it before the cancelled terminal event.

## T / Test

One deterministic fake-Xlib integration test, `research/live_control/test_executor_owner_cancel_cause_postsample_v1.py`, injects that exact ordering. The exact same test bytes were run against parent `ad7d44e5a90bc3ac6f4dce4a5a017c7c819657de` and candidate `99b7d130742b4e884709a862bc074d15e6b42ac9`.

## D / Data and result

- Parent: expected FAIL (exit 1). It emits a cancelled terminal event with `release.reason=release`, `interruption=null`, and no standalone `input_released` event; the assertion seeking that receipt raises `StopIteration`.
- Candidate: PASS (1/1, exit 0). It emits a verified `input_released` event with `reason=cancelled`, empty `keys_down` and `buttons_down`, and `published_ns < terminal_ns`.
- Candidate compile and `git diff --check`: PASS (exit 0).
- Test SHA-256: `6195b0469dccbf48fa3ab204e54b401dacd27ffd9dcf7f1657d45e64ff641f3d`.
- Shared fixture SHA-256: `e196095fcb84b21e10c48fecf155b2c4ba699d09b3299f168f069bb4d7574cea`.
- Candidate owner SHA-256: `7cc6b3bcac201624992657203cbb9459120956ad65c1fb6e56e4ac85aafad8f2`.
- Parent owner SHA-256: `662f28840bd9a84a51611a2da23681c5fec53d2b6ab00b78675a9380855c8077`.

## C / Claim boundary

This establishes a regression distinction for one forced interleaving in the existing fake backend. It does not measure race frequency and does not establish physical input release, a real X server/window-manager path, game behavior, model/task effect, human-tempo safety, or end-to-end realtime-control success.

## U / Unresolved and STOP

- Container-first execution was attempted, but the local OrbStack Docker daemon did not have `python:3.14` available. No image pull/build or container run was performed. The test was run on the host (macOS arm64, Python 3.14.5); container parity remains unverified.
- Do not claim the overall #59 live-control gate is complete. The independent live CPU/X11/game/model lane remains separately owned and was not used.
- STOP: do not merge this test PR until its parent PR #7440 is reviewed/integrated and the stacked-base relationship is rechecked.

## Reproduction

From the repository root:

```sh
python3 -m unittest -v research/live_control/test_executor_owner_cancel_cause_postsample_v1.py
python3 -m py_compile research/live_control/test_executor_owner_cancel_cause_postsample_v1.py
git diff --check
```

Expected on candidate: test passes. On the parent source revision: expected failure at the missing `input_released` assertion.
