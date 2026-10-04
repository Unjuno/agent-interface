# Preserve primary input-error ownership (#57)

An input stream error was forwarded to the Readline Interface before the existing input listener could route it through owned cleanup. With no Interface error handler, Node exited on an unhandled event. One added listener sends that error into the existing failure/close path, which observes the same accepted promise. No command is retried or implicitly cancelled.

The production change is one line in `runtime/host_v1/primary_stdio.mjs`. Two regressions are added to the existing stdio module already selected by `native-mcp-v1.yml`; workflow triggers/selections, config, schemas and defaults are unchanged. The stream owner rejects after retaining the original success or command-error response. Existing `runPrimaryStdio` then attempts original-relay cleanup; this study does not claim a new actual relay/input-error cleanup run.

## Retained result

- Test-first exact source:14 methods,12 pass/two unhandled-error failures, exit1. Minimal repair:14/14, exit0. Original private sources/logs/UTC/exits remain; public derivatives map only workspace/temp prefixes in [PROJECTIONS.json](PROJECTIONS.json).
- Source commit `8410d2b60877e5f50b7c0dea18ef0f72eb390eeb` precedes one [FREEZE.json](FREEZE.json) comparison at exact base332da58: two source arms × four schedules, eight actual Node children. [Original raw](evidence/raw.json),8310 bytes, SHA256 `362f60bda2c9fe7ac513302beb8c8f147267ea658509eefbac75fc4bafd970de`, is unchanged. Child exits are `[1,1,1,0,2,2,2,0]`.
- Baseline has three unhandled Interface exits. Candidate preserves both accepted pending outcomes, rejects before-request input failure with zero calls, and retains normal EOF behavior. An input failure is not proof that earlier input had no effect or was cancelled.
- One standalone [raw-only audit](evidence/audit.json), actual exit0, reconstructs all eight rows and rejects eight directed corruptions, including incomplete rows, premature owner rejection, missing response, replay permission and bool/float count aliases. No producer/runtime import or comparative replay.
- Relevant existing stdio/exchange/relay-host checks pass42/42, exit0, after materializing the exact timing helper. The first sparse-checkout result41/42/exit1 is preserved as a missing-dependency failure. The frozen comparison is unrelated and was not restarted.
- Author-only preparation against immutable PR6902 head f497a9fa is conflict-free tree `d73a888e3af5e025bc18d56051a6f01de585e4a0`, with17/17 combined stdio/backpressure tests, exit0. It is not a nonauthor vote, actual-main certificate or adoption of that pending repair.

All counts are exact dimensionless integers. UTC timestamps record runs; event-loop barriers are authored ordering controls, not elapsed-time or physical deadline measurements. Platform: macOS27.0.1 arm64, installed Node26.7.0; Python3.14.5 only orchestrates/audits. Binary/source/arguments are pinned; full inherited-environment isolation is not claimed. The1MiB output budget was verified against actual8310-byte raw, not enforced as a general hostile-output collector limit.

Current-base wording in preexecution comment5965115525 was inaccurate: main had already advanced403a before it was posted. Correction5965120153 preserves the332da source freeze. Relevant host/workflow blobs were unchanged; neither candidate nor audit was repeated. The earlier tool-only reproduction against PR6902 motivates the fix and lacks separate construction UTC receipts; it is not the decisive evidence.

## Scope and reproduction

Responsive sink and inert exchange only. No native backend/relay effect, physical input/release, GUI/model, task success, concurrency, timing benefit, global byte limit or permanently stalled-I/O deadline. Node22/24, Windows/device faults and actual CLI input-error cleanup remain unexecuted. Preserve the original comparison; do not reuse its occupied output path.

Ordinary regressions: `node --test --test-concurrency=1 runtime/host_v1/test_primary_stdio.mjs`. Retained-data inspection: `python research/integration/primary_input_error_57_20261003_01a0ff53/audit.py research/integration/primary_input_error_57_20261003_01a0ff53/evidence/raw.json`.

[Plan](PLAN.md), [result/limitations](RESULT.json), [prospective pins](SOURCE_PINS.json), [check dependencies](CHECK_DEPENDENCIES.json) and complete SHA256SUMS preserve provenance. No main update has been attempted. Fixed nonauthor content consensus, exact current-main tree verification, actual GitHub conditions and one expected-old forward application remain separate gates.
