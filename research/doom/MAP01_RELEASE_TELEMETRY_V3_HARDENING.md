# MAP01 release telemetry v3 hardening

Status: **OFFLINE PASS — MAP01 LIVE INTEGRATION STILL GATED.**

Task: `O3-G4-RELEASE-TELEMETRY-V3-001`  
Base: `9aed27c74c968bec71ef2e3fdf965d43332a8dd5`

## Why v3 is required

Retained v2 fixed the major v1 measurement perturbation by moving the owner-state sample after the final key release. A source review of the concurrent draft repair exposed two remaining live-blocking issues:

1. **stale-cleanup attribution:** if an explicit cleanup `up` is requested after lease expiry, cancellation, or focus invalidation but before asynchronous owner-release evidence is recorded, owner-empty state alone is insufficient to call that edge an ordinary release;
2. **analyzer compatibility:** the retained direct MAP01 analyzer consumes verified per-key `input_release_transition` rows. The retained v2 aggregate-only event would require a new analyzer rather than preserving the already reviewed contract.

V3 keeps v1/v2 immutable and hardens only these proof obligations.

## Construction

### `input_transition_owner_v3.py`

For `up` / `button_up`, the wrapper performs no owner/X11 state query and no event publication. It records:

- caller timestamp before the unchanged InputOwner v10 call;
- cheap local lease state at request time: deadline-valid, cancel-requested, focus-invalid;
- caller timestamp after v10 returns;
- owner and intent identity.

`ordinary_release_candidate` is true only when the lease was still time-valid, cancel had not been requested, and focus was not already invalid at the release request. Parent-contract and monotonic-clock anomalies fail closed.

### `doom_retained_input_backend_v3.py`

The adapter isolates a receipt batch per executor step. Per-key receipts are buffered. While another backend-held key remains, the adapter performs **no state sample and no publication**.

After the final key release it performs one `input_state` sample and verifies:

- sample starts no earlier than the last release-call return and ends no earlier than it starts;
- sampled owner identity matches every receipt;
- every receipt has the current intent token;
- owner-owned keycodes are empty;
- every release was backend-owned before cleanup;
- every receipt is an ordinary-release candidate.

Only then are the buffered rows published. They retain `event=input_release_transition`, `operation=up`, key, intent token, caller release bracket, and `owner_transition_verified`, so the retained `analyze_map01_direct_retained_input_v1.py` event contract remains directly consumable.

A raising/incomplete step discards its thread-local receipt context; a non-step cleanup releases input but emits no provenance-incomplete normal-release telemetry.

## Deterministic container gate

Commands:

```text
python3 -m py_compile input_transition_owner_v3.py doom_retained_input_backend_v3.py \
  test_input_transition_owner_v3.py test_doom_retained_input_backend_v3.py \
  probe_x11_release_batch_v3.py
python3 test_input_transition_owner_v3.py
python3 test_doom_retained_input_backend_v3.py
```

Results:

- wrapper: **8/8 PASS**;
- backend: **11/11 PASS**;
- total: **19/19 PASS**;
- `py_compile`: **PASS**.

The regressions cover ordinary release, expired/cancelled/focus-invalid cleanup rejection, parent-contract and monotonic-clock failure, exact two-key `up -> up -> sample -> emit` ordering, sample-time inversion, owner identity mismatch, nonempty owner state, stale backend ownership, intent-token mismatch, non-step cleanup, partial-batch discard, key-down preservation, and retained direct-analyzer event-shape compatibility.

## Xvfb development experiment

Conditions:

- Python 3.13.5;
- Linux 6.18.44 x86_64;
- Intel Xeon Platinum 8370C @ 2.80 GHz;
- process affinity: 5 logical CPUs (`0..4`);
- Xvfb 800x600x24, `-ac`, local UNIX socket;
- 500 single-key batches plus 500 two-key batches.

Every batch presses the key set, verifies it physically down through `XQueryKeymap`, executes the release sequence with no owner-state sample between releases, then performs the first owner-state sample and verifies all keys physically up. Publication is modeled only after that sample.

| Metric | single key | two keys |
|---|---:|---:|
| physical down verified | 500/500 | 500/500 |
| physical up verified | 500/500 | 500/500 |
| exact operation order | 500/500 | 500/500 |
| verified telemetry batch | 500/500 | 500/500 |
| release-call bracket median | 56.284 µs | 55.000 µs |
| release-call bracket p99 | 277.123 µs | 385.406 µs |
| batch window median | 56.284 µs | 114.107 µs |
| batch window p99 | 277.123 µs | 535.839 µs |
| post-final-release sample/publication delay median | 25.559 µs | 24.847 µs |
| post-final-release delay p99 | 292.265 µs | 152.904 µs |
| between-release local gap median | — | 1.034 µs |
| between-release local gap p99 | — | 1.955 µs |

The two-key between-release maximum was 25.039 µs. There is no X11 query or telemetry publication in that gap. Post-batch work occurs only after the final release and therefore does not extend the commanded hold, although it can delay later feedback.

These timings characterize this development Xvfb environment only. They are not MAP01/VizDoom latency and are not hard real-time bounds.

## H / T / D / C / U

**H — falsifiable hypothesis.** A release-telemetry layer can preserve back-to-back multi-key release semantics, reject stale cleanup, and remain compatible with the retained direct analyzer without introducing owner/X11 work between releases.

**T — minimum test.** Execute deterministic stale-state/identity/order regressions, then run 500 single-key and 500 two-key Xvfb batches requiring physical down/up verification and exact operation order with the first sample only after the final release.

**D — decision.** **PASS** for v3 offline construction and development Xvfb instrumentation. **UNCERTAIN** for MAP01 runtime integration because no VizDoom session was executed under this lease. Recovery-policy testing remains blocked.

**C — break modes.** Caller scheduling can widen the bracket; an unmodeled authority-loss mechanism could evade the cheap local stale-state flags; owner bookkeeping is not continuous physical keyboard state; the post-batch sample can delay the next observation; Xvfb timing can differ under capture/model load.

**U — uncertainty.** The exact internal X11 transition remains interval-censored by the caller bracket. Physical state is sampled after the batch, not continuously. MAP01 integration, scorer isolation, polling cadence, and useful-effect timing remain unmeasured.

## Next gate

Freeze one provenance-complete MAP01 telemetry session that selects v3 and integrates the already-retained independent progress-clock contract without exposing scorer-only state to the controller. Only after source/provenance audit should a **new allocation ID** authorize one no-retry telemetry validation. Existing v38/v39 allocation IDs remain immutable. No recovery-vs-coast efficacy comparison is admissible before that validation passes.
