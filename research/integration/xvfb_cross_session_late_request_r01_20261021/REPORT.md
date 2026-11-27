# Same-Xvfb fresh-session discriminator (r01)

This is one isolated Linux Xvfb integration run from PR #9341, not a production task-success claim. The raw JSON is the unmodified workflow artifact; the image is the observation captured by that run.

- Run: https://github.com/Unjuno/agent-interface/actions/runs/39680962152
- Commit: 9999b24dea3470f51e986d98fe95657142548f9c
- Xvfb: 2:21.1.22-1ubuntu1.3, SHA-256 97623d8c3972051fa29db5a91f64439b418a1ebc63ce449193556fc33900048e
- Scenario: the prior guarded input owner is retired while its cancellation remains UNKNOWN, late_server_request_possible=true, and replay remains forbidden. A fresh MCP server sends c to a distinct synthetic window on the same X server.
- Independent task oracle: pass; property was [0] before input and [3] after input and at the horizon; all a/b/c keymap reads were up.
- Late old keypress in the fresh task: not observed. This run demonstrates bounded fresh-task execution under a retained unknown fence, but does not demonstrate contamination from a late old request.
- The runtime task_success remains null; the passing boolean is the separate test oracle.
- Old cancellation release confirmation remains false even though the release attempt's independent readback was verified. Do not conflate those fields.
- RAW.json SHA-256: be251a4202d3a9ee04232507784affbc31fe711519ea6ee352ea8af46932193d
- observation.png SHA-256: f43c64e5c9b85707a5e8838e8f2f1b97e452ad0da32f77be81936243ffcea9ef

The separate prestarted-cancel-xvfb job in this run also passed. Windows local validation of the integration module reports the Xvfb-only case skipped by platform guard; the Linux workflow is the execution evidence for this scenario.
