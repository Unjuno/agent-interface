# X11 absolute pointer relocation distance R1 — result

Decision: **PASS_X11_ABSOLUTE_RELOCATION_DISTANCE_FLAT_SCOPED**

Direct parent #1654 / PR #1680; conceptual parent #1643 / PR #1649.

## Question

Does one existing absolute XTEST pointer relocation on private X11 expose a material issue-to-XSync-return cost increase as displacement grows, or is the current backend primitive effectively distance-flat at this fixture scale?

## Formal result

One source-frozen private-Xvfb allocation; 100 balanced blocks; distances {1,8,64,256}px once per block; **400 rows** total; formal invocation1/reruns0.

All rows independently read back the exact requested root pointer target and a neutral button mask: **400/400 exact, 400/400 neutral**. Cleanup PASS.

| distance | n | p50 | p95 | min | max |
|---:|---:|---:|---:|---:|---:|
| 1 px | 100 | 0.023765 ms | 0.033289 ms | 0.022704 ms | 0.105095 ms |
| 8 px | 100 | 0.023875 ms | 0.029734 ms | 0.022814 ms | 0.125335 ms |
| 64 px | 100 | 0.023725 ms | 0.037345 ms | 0.022723 ms | 0.057244 ms |
| 256 px | 100 | 0.023720 ms | 0.026790 ms | 0.022914 ms | 0.059859 ms |

Frozen materiality gates:
- class-median spread <=0.25 ms; observed **0.000155 ms**;
- class-p95 spread <=0.75 ms; observed **0.010555 ms**.

Independent audit PASS/errors[]. Source rehash5/5 exact.

## Construction chronology

The first excluded construction stopped before any measured row because Python-Xlib attempted to read a missing Xauthority file. Formal remained0. Setup-only repair created an explicit empty Xauthority for the private no-auth Xvfb; H/T/D/C/U and timing gates were unchanged. The repaired construction verified absolute exact readback4/4 and a stepwise 256-request path slower than the 8-request path; construction timings were excluded from threshold choice and formal pooling.

## Retention

`FORMAL_ROWS.json` is retained losslessly as deterministic gzip(mtime=0) + Base64 chunks. `RECONSTRUCT.py` verifies every chunk SHA-256, the compressed SHA-256 and the reconstructed raw SHA-256 before writing the original 400-row JSON.

- raw rows: 106,265 bytes, SHA-256 `f124d1c0163ec6b1d8111f4e69be940998a8161343e7638d5e7ed4afa3ea5746`
- gzip: 7,800 bytes, SHA-256 `7a7ee465b14a5efecdb7f404ddd69fcacda837c89e9c4ea2f6269404caa2345c`
- RESULT.json SHA-256 `a0fb1e6de0b1d146b06250d60dd2c0f38e1e29c58e321d2612e97d0dd34e04bf`
- AUDIT.json SHA-256 `6a6f9e45749fb8499475b876562e9e9e262dea9bf71ea9b78f3b85fec5df10ea`

## Interpretation

At this private Xvfb/Python-Xlib/XTEST boundary, a single absolute pointer move is extremely distance-flat over 1–256px at the measured issue-to-XSync-return endpoint. Therefore physical endpoint distance alone is **not evidence for implementing parked logical cursors on this backend**. #1654's positive switch/warp benefit is already supplied here by the existing absolute relocation primitive rather than by cursor multiplicity.

This does not test real hardware motion, Wayland, remote desktops, application hover/path semantics, semantic target re-grounding, visual cursor identity, multiple independent seats, or application effect completion. XSync is a server-processing endpoint only. Any remaining multi-cursor value should be tested separately through independent actuator resources (#1643) or semantic target-reuse/currentness mechanisms, not attributed to physical pointer travel on this fixture.
