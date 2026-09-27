# Formal successor allocation 03 — #3518

## Disposition

**PASS for the preregistered synthetic GTK/X11 gate.** Allocation `issue3518-resident-gtk-incremental-03` ran once, with correct embedded ID, and produced all 32 rows. Independent audit passed every row, all 64 retained before/after raw window-frame blobs, action indices/counts, title/task-effect state, all 32 key releases, and per-process PID/start-time/exit/reap evidence. No retry or tuning.

## Results

Policies, in order: RESIDENT_INCREMENTAL / LAST_MESSAGE / MESSAGE_COUNT / RESTART_REPLAY_UNGUARDED. Per-case transport-count vectors:

| Case | Counts |
|---|---|
| valid | 1 / 1 / 1 / 1 |
| true_then_revoke | 1 / 0 / 1 / 1 |
| revoke_first | 0 / 1 / 1 / 1 |
| replacement_delayed_old | 0 / 1 / 1 / 1 |
| out_of_order_false | 1 / 0 / 1 / 1 |
| duplicate_true | 1 / 1 / 2 / 2 |
| restart_replay | 1 / 1 / 2 / 2 |
| effect_off | 1 / 1 / 1 / 1 |

The candidate title/task-effect vector was 1,1,0,0,1,1,1,0. Window-frame byte hashes changed on precisely rows with positive effect and stayed unchanged on refusals/effect-off. All candidate causal expectations matched: a later revoke did not erase the earlier rising edge; revoke-first, replacement with delayed old generation, stale sequence, duplicate rising edge, and old-generation replay after restart behaved as frozen. Effect-off generated transport but no GUI task effect.

A separate post-run bytewise comparator (`audit_frame_pairs.js`, no reducer import) independently compared the actual 32 frame pairs against the recorded effect count: 32/32 matched, 0 mismatches.

The other allocation history remains immutable: allocation 01 is STOP before any row; allocation 02 remains a HOLD with its allocation-label, pixel-evidence, and cleanup-ledger deficiencies. Allocation 03 is a distinct corrected successor, not a rewrite or reinterpretation.

## Reproduction / integrity

OrbStack Docker; image `agent-interface-2972:20260920`, ID `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, linux/arm64; `--network none`; source mounted read-only. GTK fixture and Xvfb were separately started for every row. Each record has unique PIDs, `/proc` start ticks, GTK exit `-15` after requested termination/reap, Xvfb exit `0`, and successful reap. XTEST Space key release was read back for all rows.

- `runner.py`: `2e721ce19a3da13c2635d32ca0f7f406162304f747411d40a5fbfb14aba084f3`
- `fixture.py`: `97467cc1685b7a7bfecda3a789f82b9e1174e75bbdf7db431d789d04159c2150`
- `audit.py`: `f5e73ea87f3b224ef0c670f5907ce5b4410c5dde537ca9506c85cc303bf3aa94`
- `rows.json`: `7ee16d706c85890563d0117aa31d1324ec25214651b611886797f95d2f070dc1`
- `images.tar.gz` (64 lossless raw X11 window captures): `14474dda0c72302e2460b879e0fe86e074f2a2c105dfa728527a681d9d5abb2c`

## Scope limits

Finite synthetic local GTK/X11 traces only. No real Codex window, MCP event stream, model call, human task success, end-to-end agent benefit, production transfer, latency, cost, safety, or broad reliability claim. Independent auditor is the reported gate; CI repeats the deterministic row audit, not the GUI allocation.
