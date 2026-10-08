# Pre-compute freeze — partial-admission MAP01 occupancy posthoc v2

Task `MAP01-HELD-OCCUPANCY-PARTIAL-POSTHOC-20260916-002`; Issue #443.
Immutable publication BASE `8176db65ae5ee0e742581ff5cff50d01d7a8155b`.
No complete retained v38/v39 log computation has run at publication of this freeze.

## Exact tested source identities

The authoritative source is the GitHub branch bytes, not the earlier local transcription. Branch-only construction Actions run `35098614517` / job `104802092381` checked out head `b291ceae409cd9d7eb95385f1e9ddd5b16a7425f`, py-compiled the published sources, ran the published semantic tests **7/7 PASS**, and emitted these SHA-256 values:

| file | Git blob | SHA-256 |
|---|---|---|
| `analyze_partial.py` | `7bb32c5a26710b45b97b8dcd7cebaf160970e4a4` | `fe21e5b6d5d5e36f46eb74826d0f7abde5cac9ce8346278f22f0d5facc3cab9d` |
| `test_partial.py` | `b8b24ce1e1a4191f8e8dc2faef3b557ec6ec7ab8` | `ea4093d0eeb29e56ed88621ca20bd970f2ab795cc2c6922511ceaa6a3660a78d` |
| `audit_partial.py` | `164d386da8713d6a8fdca3e0f9b0d7dc179fad40` | `5e447d8f087f99f31f31d6bac7a406b82650a469a9e6415a47ae84e671f6ebf5` |
| `run_full.py` | `cfa2f5e77c70c82ec73452dfda8d0ac2d77b39a9` | `2b2b903ae2c70f481e34090059c2cdadeaf5983f8e1f2a1d81b24f2b33957a82` |

No full retained event log was included in the construction sparse checkout.

## Frozen semantic delta

Only hold steps interrupted **before** `keys_held` are new:

1. no `input_admission` before verified-empty termination → `zero_admission_interrupted`, any-key occupancy exactly `[0,0]` under the retained runtime event contract;
2. a strict prefix of requested keys admitted, no `keys_held`, then verified-empty release → `partial_admission_interrupted`, lower `0`, upper earliest `admitted_ns` to earliest independently verified empty release;
3. every requested key has an admission record but no `keys_held` marker before verified-empty interruption → `full_admission_no_marker_interrupted`, same conservative any-key interval, but `full_keyset_established=false`;
4. interruption after `keys_held` → v1 semantics unchanged;
5. normal completed hold → v1 semantics unchanged.

The exact retained #428 counterexample `cover-4:10` is frozen in `test_partial.py` and must produce upper bound `13.209 ms`, lower `0`, `full_keyset_established=false`.

## Frozen retained inputs

- v38 report SHA-256 `7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58`
- v38 events SHA-256 `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3`
- v39 report SHA-256 `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`
- v39 events SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`

Any source mismatch stops the computation.

## Frozen decision gate

Exactly one complete-log compute attempt is allowed. The diagnostic gate is inherited unchanged from #428:

For **both** runs:
- aggregate interval width / total model-wait `<= 0.10`; and
- aggregate interval width / aggregate occupancy upper bound `<= 0.25`.

Both runs passing → `RETAIN_FULL_OCCUPANCY_INTERVALS_SCOPED`.
Integrity-valid but either ratio too wide → `SCHEMA_CENSORING_TOO_WIDE`.
Any source, ordering, inventory, interval, or independent-audit contradiction → `FAIL_INTEGRITY`.

This is physical **any-key** occupancy only. It is not full-keyset/intended-policy occupancy, independently useful control, or gameplay efficacy. Ordinary normal key-up remains un-timestamped.

## Compute infrastructure

A temporary branch-only workflow may sparse-checkout only the new research directory plus the exact v38/v39 report/event files, run `test_partial.py`, then `run_full.py`, then `audit_partial.py`. Shell must use `set -euo pipefail`; failure evidence must upload with `if: always()`. The workflow must be deleted before result PR. No retry or source/method/gate change after the first complete-log attempt.
