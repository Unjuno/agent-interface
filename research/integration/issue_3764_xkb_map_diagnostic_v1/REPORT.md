# Issue #3764 formal-01 — PASS_DIAGNOSTIC

The one-shot pinned OrbStack allocation completed all four rows with no setup errors. The frozen runner returned `PASS_DIAGNOSTIC`; independent artifact audit is pending.

Across all three fresh German Xvfb servers:

- `setxkbmap -query` reported `layout: de` after the single application;
- the `xkbcomp -xkb` server dump changed from baseline;
- two newly connected Python-Xlib clients agreed on the complete `get_keyboard_mapping` core map, and its canonical SHA-256 changed from `664c275f5552ea7c1e752aebe65ad651c81a3682219d085deef40ee4f599e159` to `4c7f1207298544bfdac24be2993fbfee9ecdc4644d47e7308f6b1f3ee599a82b`;
- the Y and Z symbol assignments swapped physical keycodes 29 and 52. Equal and asterisk placements were also retained in the raw per-level symbol tables.

The fresh US control remained unchanged in both xkbcomp and Xlib map hashes. All four Xvfb processes were reaped. No candidate backend was imported and no XTEST/key/button/text event was sent.

Raw SHA-256: `45a7cb25a9854b5ccee6ffbd712e1ade381fb25f5f1041657eec0fac3c7d7604`. The container stdout/exit log is separate at `container-logs/formal-01.stdout.log`, SHA-256 `49d22d55e127baff1d49772d4237bc28a3e174d3d140f10a1a6d377304880740`.

This shows that the effective server dump and fresh Xlib core map agree and change under the frozen setup; the earlier unchanged-client-map observation was not reproduced. It does not identify the exact reason for that earlier observation or establish German text delivery/candidate correctness.
