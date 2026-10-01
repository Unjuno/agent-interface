# Retained MAP01 input-edge availability inventory

## H / T / D / C / U

**H:** The retained v38/v39 event streams contain key-down admission/held acknowledgements and terminal verified-empty release bounds, but no direct ordinary per-key key-up timestamp or stable physical actuation ID. The one v39 `input_released` row is an exceptional mid-run revocation receipt rather than ordinary completion telemetry.

**T:** Read-only JSONL inventory of v38 and v39 raw event streams. The payloads were fetched from main `f65b39b6434714a08dfa743f8a16f5cae1667f6d`; later current main `0a213fdb794d7c2498868fb109b1794465b70489` has the same Git blob IDs for both event files, confirming unchanged inputs at PR intake:

- `research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl`, SHA-256 `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3`; Git blob `02d65d49b61feadbdec2e051bd23d1ca845d5df1`.
- `research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl`, SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`; Git blob `cbaeed9c7ba27b53cef9d10730ae33313371ad9a`.

**D:** Final primary inventory and the separate recursive raw auditor exited 0 against these exact repository paths. v38: 340 event rows, 11 `input_admission`, 11 `keys_held`, 0 `input_released`, 7/7 terminal records independently verify empty keys/buttons. v39: 634 rows, 39 admissions, 28 `keys_held`, 1 `input_released`, 9/9 terminal releases verify empty keys/buttons. Direct `key-up`, `key-release`, `actuation_id` and `physical_edge` markers: 0 in each raw file. Disposition: `PASS_RETAINED_TRACE_EDGE_AVAILABILITY_AUDIT`; actual ordinary held-key durations cannot be recovered from these records.

**C — preserved construction stops and repairs:**

1. The first parser attempt stopped before parsing because I transcribed one expected v38 SHA incorrectly (`...fbd9bb2...` rather than `...fbd0b2...`). Preserved: attempt-1 source SHA-256 `228501a99b2b5062355dd569bd14c17583174a92d99f4e39f72cecee89faf950`, error-output SHA-256 `1fb325a54f3e53e199372dc95aaf82bb6153c6e6554bca7172eeff7d29af17f5`, exit 1.
2. The first published replay implementation labeled rows using each input path's basename. Temporary downloaded inputs were named `v38-events.jsonl`/`v39-events.jsonl`, but repository paths both end in `events.jsonl`; a replay from the new checkout therefore produced duplicate labels and failed result equality. Preserved attempt-2 source SHA-256 `c5b3c864fe48c9f9d3bcc423bdecaf0a856f6a490ce174ad8508ebe46518a89f`, replay JSON SHA-256 `b14355da0748d89825792d6d7cb495d680ca87e65c5b308b1345fb16d5fc5a87`, comparison-source SHA-256 `abbc539a08be7a4a7e76836bccd32b0b3b82e6565c1e96e6e7e0730045af203c`, and comparison failure SHA-256 `95ed20cca339182021b2f46942dcc5412e4671d3a09c860248f3316b93daddee` (exit 1).
3. The final script labels inputs by their declared v38/v39 argument role rather than basename. It was re-run from the published branch checkout against the repository paths. The corrected JSON matches the retained `result.json`; the separate raw auditor returns `PASS`. Corrected result JSON SHA-256 `7eeb1da06d7b71a8eade49b92b7b91437a31a91097adf80dcfd872f3487a24`; independent audit result SHA-256 `9eca9c4169806a23848768dc0f36cdd805ad65a54c747d7c97a4845f68648f60`.

No attempt modified either raw input, main, or any runtime source. These were reproducibility/construction repairs only; no formal allocation was involved.

**U:** A terminal empty-state timestamp is an upper bound, not the normal per-key release time; the logs do not prove continuous physical occupancy between `keys_held` and terminal. This is an instrumentation-availability result only. It makes no useful-feedback, input-safety, gameplay, latency, human-tempo, or cross-domain claim and does not clear #5156's X11/resource gate.

## Reproduction

From the repository root:

```powershell
python -B research/doom/retained_input_edge_inventory_20260928/audit_retained_input_edges.py research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl
python -B research/doom/retained_input_edge_inventory_20260928/independent_audit.py research/doom/retained_input_edge_inventory_20260928/result.json research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl
```

No model/provider, GUI, input, game, CUDA/GPU, Docker/OrbStack, or formal allocation was used.
