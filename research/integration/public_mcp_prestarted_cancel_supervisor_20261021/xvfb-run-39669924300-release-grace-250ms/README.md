# Bounded release-worker shutdown grace — Xvfb run 39669924300

**Disposition: one scoped positive release/readback result; runtime cleanup remains UNKNOWN.** This is a standard MCP caller against private Xvfb with the prestarted cancellation supervisor disabled and a test-injected delayed owner request.

## Source and conditions

- GitHub Actions [run 39669924300](https://github.com/Unjuno/agent-interface/actions/runs/39669924300), workflow `Runtime X11 v1 Integration`, job `x11-integration`; overall job passed.
- PR head `b1108350518a9a18f4227b8240d77fbc68cd0304`; workflow merge SHA `b64e799e8dfdee1e26c9fa3f5ccbe7ceb57815ed`.
- CPython 3.12.15 on Ubuntu runner; Xvfb `2:21.1.22-1ubuntu1.3`, binary SHA-256 `97623d8c3972051fa29db5a91f64439b418a1ebc63ce449193556fc33900048e`.
- `prestarted_cancel_supervisor=false`; child cancellation acknowledgement withheld for 1 second; delayed keypress horizon 8 seconds. Full frozen conditions and source identity are embedded in the raw JSON.
- `standard-mcp-xvfb-blocked-release.json` and the observation PNG are copied from the named Actions artifact without modification. SHA-256 values are in this packet and the experiment-root manifest.

## Outcome

The synthetic app committed its exact initial `a` effect while the owner was blocked in `python-xlib Display.sync()`. The owner retired with exit `-15`; an XRes disconnect worker observed the retired owner absent after 79.381 ms. The fresh release worker returned a verified all-keys-up readback and exited cleanly (`worker_exitcode=0`, `worker_retired=true`) after 603.485 ms. A separate parent X client also observed both keys up. At 8,501.456 ms after cancellation start, it still observed both keys up and no delayed `b` effect. The independent synthetic task oracle passed its exact-effect, release-readback and horizon checks.

The MCP cancel response took 301.268 ms; its recorded caller response deadline is 300 ms, so this measurement exceeded that deadline by 1.268 ms. The cancellation operation completed at 939.729 ms after admission, within the 3-second transaction deadline. Runtime `cleanup_status` remained `UNKNOWN`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false` because `late_server_request_possible=true`. The independent oracle's pass is synthetic task evidence and does not override the runtime receipt.

This run is consistent with the 250 ms clean-shutdown grace helping the fallback path, but the live result is not a matched causal comparison against 100 ms. It establishes one finite standard-caller outcome, not reliability, universal release, physical desktop control, recovery on a fresh target, or WSLc portability. No WSLc allocation was used.
