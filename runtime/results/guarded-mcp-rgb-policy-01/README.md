# Public guarded MCP RGB policy repair

The guarded public MCP owner recreated its capture sink for every call without `retain_rgb=True`. Since #5443 changed bridge observations to consume the current producer RGB, the default-disabled replacement made `interface_guarded_observe` refuse with `no matching current capture RGB handoff`. Prior direct-Python six-task trials bypassed this owner reconfiguration; their successful results do not prove the public transport worked.

The fix enables RGB retention explicitly whenever the guarded owner chooses the per-call image directory. Ordinary capture defaults, PNG verification, raw-source identity, current-frame guards, file retention and release behavior remain unchanged.

Baseline source: `1e34cef0b9c9b729aa0fbd32785dd658a4b6c94f`. Tested candidate source: see `source-revision.txt` in `raw.tar.gz` (commit `2da8bcfc2`). Both portable archives and build manifests are retained. The candidate was built after committing the fix and its tests.

## Public use and failures

Two separate private Xvfb/Openbox allocations ran the same Tk entry/Save fixture. The primary agent chose coordinates from the delivered full image and used the maintained Node host -> packaged public relay -> MCP SDK stdio -> public guarded owner -> bridge. The baseline stopped after its input-free observation refusal; it was closed and its allocation ended. The candidate completed one task with ten public calls, seven delivered images and 21 native bridge observations. This is a construction/regression case, not a matched baseline speed comparison or the six-task acceptance study required by #2789.

| Candidate call | Outcome |
|---|---|
| Observe | Fresh producer RGB and full PNG delivered |
| Mint two references | Entry border and Save text chosen from primary image |
| Input with incorrect `value` field | Invalid text refused, zero backend emissions |
| Correct `text` input | Completed/released, but image showed missing first character |
| Keyboard repair with Control-a | Completed/released, but Tk moved to start rather than selecting; image showed concatenation |
| Keyboard repair with Home and Shift-End | Image showed exact `rgb_public_01` |
| Save once | Image showed Saved; independent JSON had exact value and saves=1 |
| Original empty entry reference | Changed pixels refused before admission, no input dispatched |
| Results lookup | Full saved receipt, operation_invoked=false, no input replay |
| Close | Verified no held keys/buttons; connection and relay closed |

The two semantic repair failures are preserved, not counted as initial task success. Explicit fixed waits/gaps in corrective requests are caller choices; they do not acknowledge redraw or establish a new default. Initial character loss remains unresolved as a general input-timing problem.

Candidate SDK call entry-to-return durations in call order were 130.482, 19.820, 84.337, 170.212, 439.855, 405.081, 209.992, 91.065, 14.508 and 41.564 ms. These include SDK/server work and exclude primary reasoning/render/perception; the faster calls cannot be presented as human-tempo decision latency. Both outer fixture processes exited 0. Private child cleanup codes were Xvfb=0, Openbox=1, Tk=-15, explicitly retained rather than reported as uniformly clean child exits. Both public relays exited 0.

## Verification and telemetry

The added regression traverses the public guarded owner with real X11 capture-sink policy, real PNG/RGB production and real bridge observation; only the external display capture/binding is controlled. It verifies repeated directory changes, exact pixels, retained image equality and read-only lookup. Disabling the owner's RGB policy reproduces the refusal. An initial test expectation incorrectly used `returned` instead of public `observed`; corrected before/after logs are retained along with the original failure.

- Guarded MCP suite: 17 passed.
- Shared native protocol suite: 318 passed; harness: 135 passed.
- Capture-artifact boundary: 10 passed.
- First native run: protocol passed, harness had 31 errors due to missing numpy in the validation venv. Installed CI-pinned numpy 1.26.4 and retained a separately identified passing run.
- Host setup mistakes (precreated evidence directory, missing relay `--` separator, failed REPL assignment) happened before the successful baseline public request; empty directories and terminated relay stderr/exit records are retained. They did not cause a second GUI input attempt.

`model-usage-projection.json` retains twelve matching local primary-host execution log records with one unique token_usage_record each before the matching outer tool output. It includes setup failures and calls bundling more than one SDK operation; it is not a one-to-one SDK-call dataset. Local context reported gpt-6.1-sol. Association is ordinal within the local log, not a provider foreign key. Usage covers the entire conversation context and output, including cached input; it does not isolate screenshot/receipt tokens. The raw private conversation log and account limits are not published. Dollar cost, provider weight attestation, causal token savings and model-visible/perception timing are unavailable.

Run `python3 -O runtime/results/guarded-mcp-rgb-policy-01/verify.py`. The verifier reads the archive without extracting or executing it, checks exact file hashes, package source, every public call, PNG/raw links, release/refusal/effect/cleanup accounting and local usage consistency. Its scoped PASS does not satisfy #2789 overall acceptance. Frozen previous evidence and HOLD conclusions remain unchanged.
