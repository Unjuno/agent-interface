# Calc comparison: launcher-duration recount

This re-audits the existing d01/d02/d03 packet in `../wslc_calc_varied_pair_329_517_20261031`, without a new GUI or model run. The original audit verifies the fixed inputs, independent FODS values, distinct model calls and input release. This recount adds the recorded host-side launcher interval, from immediately before starting host and container processes until both have returned.

| Existing run | Recorded task interval | Host launcher interval | Input tokens |
|---|---:|---:|---:|
| d02 fresh regrounding | 10.220 s | 15.281 s | 25,793 |
| d03 compiled continuation | 7.961 s | 10.360 s | 12,203 |

The compiled launcher interval was 32.20% shorter in this one fixed-order pair. The shared d01 passive reference launcher took 4.547 s, but manual creation of its expected-value fixture and other preparation were not timed. Both methods consumed the same reference; allocating its cost requires a reuse policy that this experiment did not record. The launcher intervals also exclude preparation before the timer, image construction and postrun audit, and there was no separate schema preflight. They are not complete end-to-end costs.

These are two separate containers on one fixed synthetic Calc fixture, with fresh first and compiled second, different route behavior, unmeasured provider/load/cache effects and no repeated samples. The reference embeds the expected values and the save is scripted; do not infer general speed, cost, failure parity, MAP01 or a full second-domain milestone. Input tokens include cached tokens and are not billing estimates. Issue 57 remains open.

Run `python audit.py` in a checkout containing the cited sibling packet. The script pins its archive and runs its original audit before extracting launcher timings; it does not reproduce unrecorded preparation or independently inspect the external environment.
