# Issue #2447 — independent raw revalidation of case 2447008

Decision: **PASS_RECONSTRUCTION_ONLY**. This is an independent reanalysis of an already executed and preserved case, not a new GUI allocation, formal row, retry, comparative result, or Issue #2447 acceptance.

## H/T/D/C/U

- **H:** The retained 2447008 recheck status can be independently reconstructed from its saved PNGs and capture timestamps; adjacent pairs above the frozen 100ms gap are ineligible, and the observer emits no input.
- **T:** Read the exact four saved recheck PNGs, nanosecond capture starts, reported status, and release records. Recompute grayscale LK flow in a separately authored verifier with the frozen ROI `[20:300,20:620]`, max 700 corners, min 80 valid tracks, pair gap <=100ms, and DROP threshold median dy <=-20px. No GUI, game, or OS input was started.
- **D:** Pass reconstruction iff reported/recomputed status are both `NO_DROP`, exactly one adjacent pair is eligible, none signals DROP, observer inputs are zero, and all 33 owner releases independently verify empty.
- **C:** Docker Desktop image `agent-interface-map01-lab:2447-preflight-20260927`, immutable image ID `sha256:b99a3444e7b2b05d159976d9ba60d9e90f212d47406c4b7aa7773e5042a28713`; Linux/amd64, network disabled, container root read-only, evidence mounted read-only, only the new report output writable.
- **U:** This does not test the `DROP_COMPLETED` allow path, physical frame-drop behavior beyond these retained intervals, failure rates, comparative benefit, held-out transfer, recovery, or cumulative episode completion.

## Reconstructed result

| Pair | Gap (ms) | Tracks | Median dy (px) | Eligible |
|---:|---:|---:|---:|:---:|
| 0 | 211.615679 | 525 | 0.0 | no |
| 1 | 112.293899 | 524 | 0.0 | no |
| 2 | 87.170655 | 519 | 0.0 | yes |

Independent code returns `NO_DROP`, matching the saved runner and prior audit. The two delayed pairs are excluded by the 100ms criterion. Observer inputs: 0. Owner releases: 33/33 verified empty. Errors: none. Formal rows: 0; retries: 0.

## Reproduction and provenance

The verifier is `independent_raw_audit.py`; machine output is `INDEPENDENT_RAW_AUDIT.json`. Both are read-only relative to the preserved original evidence. Source SHA-256: `d99791568ed4a09c5430b79f71074948cea7ac37fb83350763651fac3cf400e1`. Output SHA-256: `f7104c64bcc7953a914ab200f59339b8bc8d445eed293777bfda178e1907e058`.

Original PNGs, runner record and owner logs remain unchanged in the adjacent `../raw-evidence.zip` published for case 2447008 (SHA-256 `69736575b4e8537bf2cac232b0f560056df7266147d6c0f297dbf4061df9b3b8`).

