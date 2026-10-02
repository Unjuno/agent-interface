# #59 repeated-key occupancy representation boundary T0

## H / T / D / C / U

- **H:** The r133 per-key occupancy ledger cannot represent two distinct press/release pulses for the same key within one action/epoch. It will fail closed as `UNKNOWN`, although each pulse has a valid independent timing bracket. The missing data-model key is a pulse/interval identity, not a new measurement source.
- **T:** One deterministic synthetic action contains two non-overlapping `W` pulses, both bound to action `act-repeat-1`, epoch `9`, followed by exactly one same-action verified-empty receipt. Run the unchanged ledger from PR #6094 once. A separate raw-only auditor computes the two mathematical intervals from the frozen request/sync brackets and checks whether the candidate result can represent both. Retries: zero.
- **D:** Confirm the representation boundary only if the oracle yields two uniquely identified `W` intervals with bounds `[20,40] ns` each and the unchanged candidate returns `UNKNOWN` specifically for duplicate/invalid key. Any other candidate result is `FAIL_UNEXPECTED`; any malformed fixture, source mismatch or raw mismatch is `FAIL_AUDIT`.
- **C:** Current main `f54e7665f099e78d11cff9ca28e812782aac33d1`; candidate implementation copied byte-for-byte from open PR #6094 head `3983343f6773f118b92652c5e7f72a34b9eda7a2` (`ledger.py`). Windows host, CPython 3.12.10. CPU-only. Docker Engine unavailable at the bounded preflight; no container will be claimed.
- **U:** Synthetic representability only. No X11, keymap, physical held time, app delivery/consumption, useful effect, game, model, GUI, input, safety, latency, MAP01 success or live allocation is tested. This does not invalidate the existing fail-closed behavior; it identifies a required schema extension before repeated-pulse actions can yield per-occurrence durations.

## Frozen case

Two sequential W occurrences have independent brackets:

| pulse | press request | press sync | down sample | release request | release sync | up sample | duration bound |
|---|---:|---:|---:|---:|---:|---:|---:|
| `w-1` | 100 | 110 | 111 | 130 | 140 | 141 | 20–40 ns |
| `w-2` | 200 | 210 | 211 | 230 | 240 | 241 | 20–40 ns |

One `verified_empty` at 300 ns closes the same action/epoch. `pulse_id` is an analysis label for the independent oracle; it is intentionally not consumed by the existing candidate.

## Frozen procedure

1. Run `python candidate.py` once; retain its JSON stdout verbatim as `results/t0-01/raw.json`.
2. Run `python audit.py` once in a separate process; retain its JSON stdout verbatim as `results/t0-01/audit.json`.
3. Do not rerun either process. A correction, if needed, receives a successor allocation and path.
