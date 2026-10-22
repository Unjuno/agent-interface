# Saturated relay cancellation through standard Fake X caller — R01

**Disposition:** `PASS_FAKE_X_RELAY_COMPOSITION_ONLY`  
**Source baseline:** `12682ef54389cb3e7fe66757ed5ece64220fbde7`  
**Environment:** Windows, CPython 3.11.9. No model, WSLc, Docker, native X server, or physical input.

## Question and result

When 16 ordinary responses fill the relay's pending-stdout budget and the first stdout write is held, can `interface_guarded_cancel` still reach the standard MCP caller and run its cleanup path against an already-held Fake X key?

The composed test passed once under normal Python and once under `-O`. In both runs, the real public Relay and standard MCP server were composed with the repository's synthetic Fake X socket fixture. The owner had emitted and the fixture had accepted a key-down request; its reply remained held. Sixteen `interface_clock` requests saturated the relay response budget while the first public stdout write was blocked. The following cancel reached the MCP server before stdout resumed. The injected Fake X release callback changed the synthetic key state from down to up and returned a test-only `readback_verified` receipt. The cancel JSON response was written only after stdout resumed.

| Run mode | Cancel admission → injected release | Cancel admission → MCP return | Cancel response written after resume |
|---|---:|---:|---:|
| Normal | 0 ms recorded delta | 78 ms | 78 ms |
| Optimized (`-O`) | 15 ms | 78 ms | 93 ms |

The normal run's admission and fake-release timestamps fell in the same recorded monotonic tick; this must not be read as zero physical latency. These two interpreter modes exercise the same frozen schedule and are not two independent reliability samples. Timing is local test instrumentation, not a service-level bound.

## Safety classification and limits

The operation remained `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, `replay_allowed=false`, and `late_server_request_possible=true`; uncertainty is intentionally preserved. The fake state transition and release receipt are injected test behavior, not an OS readback. This result demonstrates that cancellation dispatch and the synthetic cleanup callback can proceed while ordinary relay stdout is blocked at its configured pending-response limit. The cancellation response itself remains backpressured until stdout resumes.

This does not prove native input release, release during blocked platform I/O, an independent physical-state observer, target-generation correctness, task success, WSLc portability, matched efficiency, or reliability. It does not establish that arbitrary queued ordinary requests can be bypassed; one bounded cancellation response slot is reserved while ordinary work stays at the existing 16-response cap.

## Reproduction and retained files

Exact source blob IDs and interpreter commands are in [`conditions.json`](conditions.json) and [`source-blobs.txt`](source-blobs.txt). The test's structured timing/state receipts and raw unittest output are retained separately for normal and optimized runs under [`raw/`](raw/). `SHA256SUMS` covers all packet and raw files except itself. No formal WSLc allocation or container operation was used.
