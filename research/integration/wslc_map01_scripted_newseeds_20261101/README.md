# MAP01 fixed-action watch controls on two further seeds

Four fresh WSLc episodes extend the [scripted watch controls](../wslc_map01_scripted_watch_controls_20261101) with seeds 991039 and 991040. The 316-file candidate matches that study's frozen manifest, but is not asserted to equal current main. Each arm uses a scripted 500 ms fire action at (636,526), a two-second pending fixture and no model call. Order was baseline/watch for 991039, then watch/baseline for 991040. Private Xvfb containers used 1 CPU / 1 GiB and no network; WSLc warned that the memory limit excludes swap.

| seed | arm | action | ammo | hits | damage | kills | health |
|---:|---|---|---|---|---|---|---|
| 991039 | baseline | completed | 50→48 | 0→2 | 0→30 | 0→1 | 100→100 |
| 991039 | watch | cancelled, partial effect unknown | 50→49 | 0→1 | 0→15 | 0→0 | 100→94 |
| 991040 | watch | cancelled, partial effect unknown | 50→49 | 0→1 | 0→15 | 0→0 | 100→100 |
| 991040 | baseline | completed | 50→48 | 0→2 | 0→20 | 0→1 | 100→100 |

The values are simulator samples bracketing the pending interval; they do not establish that a particular action caused the changes. In both watch trials, natural patch change crossed the fixed threshold and a cancellation was requested; acknowledgement did not itself verify release. Separate owner receipts verified neutral release in all four, and tested keys were up at close. The two request-start to verified-release intervals were 4.336 and 8.393 ms; they are individual measurements, not bounds. Neither watch trial recorded a kill by the second sample; the 991039 watch trial also lost six health. This is evidence that an indiscriminate visual watch may interrupt useful continued fire in these two separate episodes, not proof that cancellation caused the score or health difference or that it was unsafe.

`public.zip` preserves frozen candidate, conditions, scripted fixture, screenshots, observations, monitor crops and action/release receipts. Run `python audit.py` without -O and with Pillow to verify hashes, fixture/image associations, gate and monitor crops, cancellation/release ordering, counters and neutral receipts. Private path-bearing launcher commands remain local and are not independently audited; seed settings are recorded by conditions and launcher, not read back from the simulator. The WSLc running-container list was empty after the block.

Two new seeds and sequential independent episodes do not provide a false-positive rate, semantic threat label, controlled model comparison, general latency or reliability result. Game timing and world evolution are not synchronized between arms; the fixed target and policy are not model decisions. MAP01 completion remains unproven.
