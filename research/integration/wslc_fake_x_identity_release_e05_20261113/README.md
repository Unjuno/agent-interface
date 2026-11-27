# WSLc Fake X identity-prefix release E05

## Result

`PASS_SCOPED_FAKE_X_IDENTITY_PREFIX_RELEASE` — one WSLc execution of the frozen current-main test
`runtime.cli_v1.test_mcp_process_identity.MCPIdentityTests.test_change_after_modifier_releases_prefix_and_requires_review` passed (1 test, 0.177 s).

The public MCP call was admitted, emitted a two-event prefix, then failed closed when the target process identity changed before the next key press. The test's exact FakeX assertion passed for `KeyPress(CTRL)` followed by `KeyRelease(CTRL)`; its retained terminal report records `emissions=2`, `release.verified=true`, `keys_down=[]`, `buttons_down=[]`, `review_required=true`, `task_success=null`, and `replay_allowed=false`. A later attempt using the stale alias returned `refused/WINDOW_REVIEW_REQUIRED` with `input_dispatched=false`.

This is a useful WSLc portability check of the public MCP/session code over the in-process FakeX fixture. It demonstrates the identity-change prefix-release branch under this synthetic fixture. It is not evidence of real X-server or physical-key delivery, delayed-request recovery, an independent application task effect, WSLc desktop control, MAP01 completion, native Win32 exception handling, reliability, or speed.

## Conditions and custody

- WSLc 3.0.3.0, session 1, cached image `agent-interface-chromium:wslc-20261031-a01`, image ID `sha256:9841e60e91b1c037a8e7de6a7cb9737558352b15f052912d92af819487fe02ba`.
- Python 3.11.2; `--pull never`, `--network none`; source mounted read-only.
- One test case, one fresh container, no retry. The packet-local runner only retained `TemporaryDirectory` files and selected the one test case; it did not change test logic.
- The source test, MCP server, owned session, X11 bridge and backend blobs match `origin/main` at the recorded source SHA.
- Conditions, preregistration, invocation, stdout, exact retained test files, adjudication and a SHA-256 manifest are in the private packet `private-packets/wslc_fake_x_identity_release_e05_20261113/`.

## Preserved setup outcomes

- E01 stopped before test import because the image's Node entrypoint treated `python` as a Node module.
- E02 stopped before test execution because the sparse source mount omitted an imported research module.
- E03 stopped during supplemental-source verification; a differing module was not substituted.
- E04 imported and entered a different caller test but failed at initial observation (`KeyError: source`) before any input event, because that case did not install its FakeX observation patch.
- E05 is the fresh, passing FakeX identity-prefix-release case above. All prior outcomes remain preserved in the private packets.

## Next boundary

To advance the active computer-control goal, add a WSLc-integrated FakeX or Xvfb case for the post-recovery horizon and independently scored task effect. Native Win32 exception recovery and MAP01 remain separate live gates.
