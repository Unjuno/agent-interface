# S34 standard-caller generation, recovery and effect result

**Decision: `PASS_SCOPED` (23/23 independent checks).** One WSLc 3.0.3 private-Xvfb run passed the current-main `StandardCallerXvfbGenerationTests.test_process_and_window_generation_flow_through_standard_mcp` test. The public observation carried the expected Linux process-generation digest, a window-generation digest, and process-identity/query-worker/window-lifecycle evidence. Observation itself reported no input dispatch or side-effect authority; a fresh alias minted from its source sequence.

The test first produced exact synthetic effect `[1]` and an empty verified release receipt. Then an injected post-press acknowledgement error and one-shot automatic release error left key `b` physically down in Xvfb, with the public failed operation marked effect-unknown and recovery required. The standard recovery call issued release-only recovery; the application observed release and an independent X client read `b` up. Recovery kept replay denied and task success unknown. After review and fresh alias minting, a separate continuation produced exact effect `[3]`, with a matching keypress/keyup and an independent app-property read. The destroyed window's stale generation was refused before input (`input_dispatched=false`, target queries retired, review required); its old alias was also refused. Public close verified release and closed the owner.

## Timing observed in this replicate

| Measurement | Result |
|---|---:|
| Public observe call | 1,059.373 ms |
| X capture interval | 5.853 ms |
| Capture end to observe response | 26.103 ms |
| Mint call | 23.153 ms |
| Initial input call | 52.516 ms |
| Initial X keypress event to synthetic app effect commit | 0.082 ms |
| Faulted input call | 47.840 ms |
| Recovery call | 11.279 ms |
| Recovery start to independent all-up readback | 11.378 ms |
| Post-recovery X event to app effect commit | 0.092 ms |
| Stale-generation refusal call | 33.346 ms |

These are single-sample private-Xvfb timings. Event-to-effect measures X event delivery to the synthetic app's property write, not physical input-to-redraw latency. They do not establish a latency guarantee, broad reliability, matched efficiency, live application or MAP01 transfer.

## Evidence and custody

- Conditions, source/input hashes and complete raw mirrors are in this directory; the independent check list and calculations are in `AUDIT.json`.
- Original raw files remain under `%LOCALAPPDATA%\agent-interface-research\wslc-s34-6da84c1efb73`; their SHA-256 hashes and lengths are in `raw/RAW-SOURCE-SHA256.json`. Readable mirrors mask the local account name.
- WSLc confirms the one exact container and pulled image were deleted, the new session terminated, and the runner exited zero. No Docker or global WSLc inventory was used.
- The uniquely allocated post-termination 236,978,176-byte `storage.vhdx` remains retained. SHA-256: `9b4b647017b3c08f147752baa03c93ff63c6ac00729f6d4b9f5e17a82ca80023`.
