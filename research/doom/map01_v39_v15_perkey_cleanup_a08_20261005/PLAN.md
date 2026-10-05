# A08 pre-registration — repair the fake-owner admission fixture

Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59), the current-main V39/V15 per-key release measurement path.

**H — Hypothesis.** The A07 pre-treatment STOP came from its test-only `ControllerBackend.execute` bypassing the production session's observed-focus lease binding and per-step input telemetry context. If the fake backend supplies those two inputs from a stable fake observation while leaving the V13 executor and V15/V4/V3/V12 release implementation unchanged, the normal control should complete and one deterministically dropped first KeyRelease should be retried by the selected owner path, leaving no fake-server key down before terminal publication.

**T — Minimum test.** Against the exact current-main source freeze in `FREEZE.json`, run the two-arm candidate once: first a normal single-key DOWN/UP control, then a treatment that drops exactly the first fake KeyRelease. This is a standard-library/Pillow host run after the configured OrbStack context failed its cached-image read preflight. The controller runtime, V13 executor, selected V15/V4/V3/V12 implementation, and fake X server source stay fixed; only the test double binds the observed focus and `(intent, step)` telemetry context as `session_v7.Backend.execute` does. Retain raw output and independently adjudicate both arms. No retry.

**D — Decision.** `PASS_CONSTRUCTION_SCOPED` only if the normal arm has one explicit key-up attempt, the treatment records a first still-down sample followed by a second attempt that samples up, both terminals report one completed step and verified empty release, and both final fake keymaps are empty. Any failure before the action loop is `STOP_BEFORE_TREATMENT`; a completed but unmet release condition is `FAIL_CONSTRUCTION`. Container preflight remains separately `STOP_ORBSTACK_IMAGE_READ_UNSUPPORTED`.

**C — Competing explanation.** A07's focus failure could reflect incomplete fake-session wiring rather than a product defect. The expected result could also come solely from fake-X behavior and not match real X11 scheduling or physical input. A result with no `input_release_transition` is not a key-release result.

**U — Uncertainty.** This construction probe does not exercise a real X server, physical keyboard, Doom, game time, model, application effect, useful feedback, recovery, latency distribution, or live threat exposure. No authority for the private game lane is inferred.

## Frozen execution boundaries

- Source base: `origin/main` at `712a71b25dc024b5406b24b568225c0663e7278b`.
- Candidate: this package's `candidate.py`; source SHA-256 recorded in `FREEZE.json`.
- Production source closure: exact Git blob and SHA-256 manifest in `source-manifest.json`.
- Inputs: one normal and one injected first-KeyRelease-loss arm; each has one F8 DOWN/UP batch.
- Environment: Codex bundled Python 3.12.14 with Pillow 12.3.0 on macOS; no network or GUI/X server access by the test double.
- Output: `results/candidate.json`, written once. The auditor consumes only that retained raw file.
- OrbStack preflight: `docker --context orbstack ps --no-trunc` returned no containers; cached-image listing failed on blob `sha256:b138c00ce990cf972f8be1ae4b3f7a11a198ad46e8804b41dabd979052aad8e8` with `operation not supported`. No image pull, prune, or daemon repair was attempted.
