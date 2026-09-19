# Fresh post-effect GTK drawable receipt precheck (#2673)

This additive path preserves the STOP in #2671 and the observation-identity
preflight in #2660/#2663. It is not a formal #2606 acceptance result.

## Frozen experiment boundary

- Base commit: df2f97c49b503aea7c44f8d0bde9b58fa5cc2ff6
- Container: codex-gtk-model:local
- Display: GTK3 under Xvfb
- Python: /usr/bin/python3
- Model/provider/network: disabled
- Case order: useful, unavailable, guarded, no_effect, partial,
  stale_repair, ambiguous, cleanup_failure
- Replay: false for every case

## Required receipts

Each case must retain:

1. fresh pre-effect GTK window and drawable identity/hash;
2. declared case operation and raw input ledger;
3. independent admission, authority, lease, and release receipts;
4. fresh post-effect GTK window and drawable identity/hash;
5. independent before/after effect receipt;
6. cleanup receipt and terminal input state;
7. scorer output and raw artifact hashes.

A process exit or a fresh-window identity change alone is not an effect receipt.

## Decision

PASS_EFFECT_RECEIPT_PRECHECK_SCOPED requires independent distinction of
useful, no-effect, and partial/collateral effects, plus safe YIELD for the
five unsafe/uncertain cases, no replay, and cleanup failure never classified
as success. Any fixture, rendering, provenance, or receipt-integrity failure
is STOP/FAIL with raw artifacts retained.

No model utility, token/latency, production GTK, or formal #2606 claim is
permitted from this precheck alone.
