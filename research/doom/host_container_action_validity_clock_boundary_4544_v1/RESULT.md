# Host/container clock-domain freshness probe — 2026-09-27

## H/T/D/C/U

- **H:** Passing an Executor-container capture timestamp and a host-controller decision timestamp directly to the existing freshness guard can distort their apparent age because the two monotonic clocks may have different numeric origins.
- **T:** After recording the construction-only plan on Issue #4544, run one persistent pinned linux/arm64 container and take three host-before/container/host-after perf_counter_ns probes. Feed the third container timestamp and the host decision time to the exact current-main RunningActionGuard; separately run a host/host ordered control. Source blobs and hashes are listed below. No model, game, GUI, task input, formal allocation, or shared-runtime write.
- **D:** The pre-registered exact-inversion/ValueError gate was **not reproduced**: all three host decision values were numerically about 739.110 seconds after their container capture values. The real guard returned REJECTED_STALE/current_snapshot_too_old and transitioned the active guard to CANCEL_REQUIRED with authority false, release still unverified, and new decision required. Independently, the two container captures spanned only 2.762 ms. The host/host control remained INPUT_ACTIVE. Classification: HOLD for the expected inverted-order exception; scoped positive evidence that this host/container clock mismatch can trigger a stale rejection when raw clock values are compared without translation.
- **C:** One host and one persistent Docker process in this environment; deterministic guard fixture with max_current_age_ms=30000. It is not the #4544 formal MAP01 process or its source freeze. No actual physical input was sent. The opposite numeric offset direction also differs from the historical seed-990641 exception; do not infer that run's cause.
- **U:** Exact seed-990641 capture_ns/controller_decided_ns pair and source clock domains remain unrecorded. This result does not explain its controller-decision-before-snapshot exception, justify a runtime patch, or authorize a new formal allocation.

## Raw clock samples

All times are nanoseconds from each process's own perf_counter_ns clock. Offset intervals are host-before/container through host-after/container; do not treat either clock origin as globally comparable.

| Probe | Host before | Container capture | Host after | Host decision | Host − container interval | Decision − capture |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 14759265336541 | 14020429793516 | 14759540262708 | 14759540263333 | [738835543025, 739110469192] | 739110469817 |
| 2 | 14759540276958 | 14020430975278 | 14759541097666 | 14759541097916 | [739109301680, 739110122388] | 739110122638 |
| 3 | 14759541099875 | 14020432555656 | 14759542737083 | 14759542737958 | [739108544219, 739110181427] | 739110182302 |

The last two container captures differ by 2,762,140 ns (2.762 ms). The mixed-domain guard calculation is 739,110,182,302 ns, exceeding the fixture's 30,000,000,000 ns freshness threshold. The guard result was REJECTED_STALE; no exception was raised. The host/host positive-order control returned INPUT_ACTIVE with authority true.

## Provenance and audit

- Main source reference: 4c3d6f1240896d4441ecb37e447760a3847012ae. The exact source Git blob IDs and SHA-256 digests below were re-read from current main and were unchanged after PR #4558 merged.
- action_validity_admission_v1.py blob 31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e; SHA-256 f102cbde4f0e46c9f8e974e9f0a7d1c47f3fc662d7c8ba32699d16799d3db98a
- running_action_guard_v1.py blob d54047e78bc76f53ef47c6f70fd4a3be6318f09c; SHA-256 2d5feb69efd59fdca22e0db9e561923411490eb758eab9e2b8379714e20e5c62
- Container image issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e; linux/arm64; --pull=never, --network none, --read-only, 16 MiB no-exec tmpfs.
- The initial harness failure remains recorded verbatim on Issue #4544 as HOLD_HARNESS_OUTPUT_NOT_RETAINED; the successful corrected invocation is the source of result.json.
- audit.py independently recomputes every interval, clock difference, 30-second threshold comparison, and expected guard disposition. Run: python3 audit.py

