# First outcome — repeated-key occupancy representation boundary

**Disposition: `PASS_REPRESENTATION_BOUNDARY_SCOPED`.** The unchanged #6094 ledger returned `UNKNOWN` with `duplicate_or_invalid_key` for two valid, sequential `W` pulse records in one action/epoch. An independently authored oracle computed two separate occurrence bounds, 20–40 ns each. Candidate behavior is fail-closed and does not emit a false duration; however, the current key-unique schema cannot represent repeated same-key occurrences even when every press/release bracket and the terminal empty witness are present.

The first candidate invocation and separate raw-only auditor each exited 0; retries: 0. The auditor imported neither candidate nor ledger. Raw SHA-256: `7efcceb24c8a267e1db7b1342efe90724787e1f4371ecf28a8c599cc0c1ee9cb`. Audit SHA-256: `222dcc4669805b2954f2f1ee4371d17638bbc6433336c096332977d8d33b5ee1`.

## Interpretation for #59

Before a live action can yield useful per-key occupancy statistics for repeated pulses, the event identity needs to distinguish occurrences (for example, a stable `press_id`/`interval_id`) while preserving action, epoch, key, both timing brackets and the verified-empty terminal. Simply dropping duplicate-key rejection or merging intervals would be unsafe: it could collapse separated presses, hide gaps, or conflate overlapping key state. The natural extension should be a separate successor and should be tested against real owner/keymap evidence before any live claim.

This result does not show that v39 used a repeated-key pulse in its retained nine programs; it establishes a schema boundary only. It does not modify #6094's frozen one-shot result or imply a defect in its fail-closed decision.

## Scope and environment

The exact six timestamp fields were fixed as synthetic integer nanoseconds. No randomness or retries. Windows host, CPython 3.12.10, CPU-only. Docker Desktop's Engine query timed out at five seconds and `com.docker.service` was `Stopped/Manual`; no container ran. No X11, game, GUI, physical input, model, GPU, WSL guest workload, or application-effect observation was used. This is not a physical hold-duration, task-effect, safety, latency, gameplay, or product result.

Frozen inputs and source hashes are in `FREEZE.json` and `SOURCE_HASHES.json`; exact candidate and independent-audit outputs are in `results/t0-01/`.
