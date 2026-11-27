# Standard-caller Xvfb integration after cancellation liveness-order fix

Run: [GitHub Actions 39678104458](https://github.com/Unjuno/agent-interface/actions/runs/39678104458)<br>`nTest head: `285dc22ff751bce929e37afc94794262dbe0a310`<br>`nScope: private Xvfb, Linux x86_64, Python 3.12.15, synthetic application, public standard MCP caller. Xvfb package was `2:21.1.22-1ubuntu1.3`, executable SHA-256 `97623d8c3972051fa29db5a91f64439b418a1ebc63ce449193556fc33900048e`.

This packet preserves the two raw reports from the run. They are distinct scenarios in one CI run; neither is a reliability estimate, a physical desktop result, a MAP01 result, or a WSLc experiment. The test head includes the liveness-assertion correction for PR #9338. Runtime behavior was unchanged by that test correction.

## Generation change and recovery scenario

`standard-mcp-xvfb-generation.json` reports `PASS_SCOPED_XVFB_STANDARD_CALLER_RECOVERY`. The standard guarded caller observed a synthetic X11 target, then an injected post-press acknowledgement failure and one failed automatic release required recovery. Release-only recovery took 3.711123 ms; an independent X client read the key up. The synthetic application event loop observed the recovery effect after 35.248309 ms from input-call start. After fresh observation and mint, a new caller action committed the expected property value `[3]`, with an independent X client reading it and observing press then release; the commit followed input-call start by 40.854377 ms. A stale alias was refused, and the destroyed-window generation was refused after its target-query worker retired. The runtime `task_success` API remained null.

This is one scoped standard-caller/Xvfb recovery and generation result. It does not establish successful cancellation recovery across sessions, physical control, MAP01, or a general reliability rate.

## Blocked release and cancellation liveness scenario

`standard-mcp-xvfb-blocked-release.json` reports `OBSERVED_SCOPED_XVFB_STANDARD_CALLER_CANCEL_CLEANUP_UNKNOWN`. The owner was blocked in real `python-xlib Display.sync()`; a delayed KeyPress was injected with an 8,000 ms horizon, cancellation acknowledgement was withheld for 1 s, and the prestarted supervisor was disabled. The cancel response returned in 251.935676 ms against the 300 ms response deadline. The event-loop heartbeat maximum gap was 1.548712 ms over 204 samples.

The owner retired with exit code -15. XRes disconnect observation took 61.853794 ms. A separate release worker returned `readback_verified`, exited 0, and read all keys/buttons up after 431.080761 ms. An independent X client also observed all keys up at release and at 8.5011 s; no delayed `b` KeyPress was observed, and the synthetic task oracle passed (the one initial effect remained `[1]`, no delayed effect occurred, and both keys were up).

Runtime classification correctly remained `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, `replay_allowed=false`, and `late_server_request_possible=true`. The liveness snapshot said `alive=true` at 210217057966 ns, after caller response at 210213261476 ns but before terminal cancellation completion at 210710452863 ns. It is a timestamped observation during pending cleanup, not evidence of survival after terminal cleanup. The test now compares liveness to cancellation completion and separately requires terminal owner-retirement evidence.

The test and dedicated prestarted-cancel-Xvfb jobs passed. The separate `evidence` job failed before tests because Python 3.13.5 was unavailable on Ubuntu 26.04. No WSLc allocation or Docker was used. Do not infer that an X-server outage releases input: this run used a responsive Xvfb server while the client was blocked.

## Raw custody

The two unmodified JSON reports are in `raw/`. `SHA256SUMS` records their SHA-256 digests. The reports include source identity, monotonic stage timestamps, owner PID/resource-base evidence, independent readbacks, task oracle, and final runtime classification. Their first outcomes are immutable.
