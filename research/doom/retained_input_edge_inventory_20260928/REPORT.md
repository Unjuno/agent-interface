# Retained MAP01 input-edge availability inventory

## Question and H/T/D/C/U

**H:** The retained v38/v39 event streams contain key-down admission/held acknowledgements and terminal verified-empty release bounds, but no direct ordinary per-key key-up timestamp or stable physical actuation ID. The one v39 `input_released` row is an exceptional mid-run revocation receipt rather than ordinary completion telemetry.

**T:** Read-only JSONL inventory against the immutable inputs from main `f65b39b6434714a08dfa743f8a16f5cae1667f6d`:

- `research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl`, SHA-256 `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3`.
- `research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl`, SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.

The two Git blob IDs remained unchanged at current main during publication intake (`02d65d49b61feadbdec2e051bd23d1ca845d5df1` and `cbaeed9c7ba27b53cef9d10730ae33313371ad9a`).

**D:** The primary JSON inventory and separate recursive raw auditor both exited 0. v38: 340 event rows, 11 `input_admission`, 11 `keys_held`, 0 `input_released`, 7/7 terminal records independently verify empty keys/buttons. v39: 634 rows, 39 admissions, 28 `keys_held`, 1 `input_released`, 9/9 terminal records verify empty keys/buttons. Direct `key-up`, `key-release`, `actuation_id` and `physical_edge` markers: 0 in each raw file. Disposition: `PASS_RETAINED_TRACE_EDGE_AVAILABILITY_AUDIT`; actual ordinary held-key durations cannot be recovered from these records.

**C:** The first parser attempt stopped before parsing because I transcribed one expected v38 SHA incorrectly (`...fbd9bb2...` instead of the immutable source's `...fbd0b2...`). I retained its script/output, corrected only the expected constant in the next construction attempt, and ran an independent checker using recursive JSON key/value inspection. No allocation was consumed, no raw file or repository file was changed, and no runtime was invoked.

Attempt 1 (expected-hash typo; exit 1):
- script SHA-256 `228501a99b2b5062355dd569bd14c17583174a92d99f4e39f72cecee89faf950`
- exact captured error output SHA-256 `1fb325a54f3e53e199372dc95aaf82bb6153c6e6554bca7172eeff7d29af17f5`

Corrected inventory:
- source SHA-256 `c5b3c864fe48c9f9d3bcc423bdecaf0a856f6a490ce174ad8508ebe46518a89f`
- result JSON SHA-256 `7eeb1da06d7b71a8eade49b92b7b91437a31a91097adf80dcfd872f3487a24`

Independent audit:
- source SHA-256 `42708320dea1b328f89afeed58c8d2ce8400b56ccbb960abc03d0c2ec9f3b04a`
- PASS result JSON SHA-256 `9eca9c4169806a23848768dc0f36cdd805ad65a54c747d7c97a4845f68648f60`

**U:** The terminal empty-state timestamp is an upper bound, not the normal per-key release time; these logs do not prove continuous physical occupancy between `keys_held` and terminal. This is an instrumentation-availability result only. It makes no useful-feedback, input-safety, gameplay, latency, human-tempo, or cross-domain claim and does not clear #5156's X11/resource gate.

## Reproduction

From the repository root, against the retained files listed above:

```powershell
python -B research/doom/retained_input_edge_inventory_20260928/audit_retained_input_edges.py research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl
python -B research/doom/retained_input_edge_inventory_20260928/independent_audit.py research/doom/retained_input_edge_inventory_20260928/result.json research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl
```

No model/provider, GUI, input, game, CUDA/GPU, Docker/OrbStack, or formal allocation was used.
