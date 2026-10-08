# MAP01 v38/v39 control-tempo reconstruction (posthoc)

The two retained first-outcome MAP01 episodes were re-read without new model
or GUI calls. The analysis binds each report and raw runtime event stream by
SHA-256, reconciles every accepted cover with its submitted steps and terminal,
then intersects those program envelopes with the corresponding model-wait
window. A program with any motor `hold` is classified as motor-capable cover;
an accepted coast program with no hold is coast cover. This measures the
program envelope, not actual key-down occupancy or task-useful effect.

| Retained first outcome | Model wait | Motor-capable cover envelope | Coast envelope | No program envelope | Completed answers | Model plan admissions |
|---|---:|---:|---:|---:|---:|---:|
| v38 | 27.489 s | 11.418 s | 16.022 s | 0.049 s | 2/6 | 1/6 |
| v39 | 43.318 s | 21.821 s | 21.484 s | 0.013 s | 5/6 | 3/6 |

V39's unauthored coast decisions2 and3 spent6.307s and6.725s respectively
inside a coast program while inference continued. Exact early typed samples
show health85→73 and73→68 in those two model waits. Their model answers
completed; decision2's action was still rejected at fresh immediate validity,
and decision3's action entered the running path. The v39 repair prevents the
previous redundant planner interruption. It does not itself make the
21.484s coast envelope motor-capable or demonstrate that waiting safely
preserves health. A future recovery cover needs a distinct explicit task and
safety rule; reusing an expired authored policy by silently rebasing its loss
budget would expand its authority.

The one v39 active revocation is a separate reaction sample. The typed health
frame that rejected decision3's running predicate was captured 38.844ms before
physical empty-input verification; its typed event was emitted 26.090ms
before verification, and terminal closure followed another52.961ms later.
These timestamps are bound to the same plan ID, evidence sequence and matched
release. They establish a local reaction boundary for one event, not a
distribution or human-tempo equivalence.

The earliest exact plan frames were captured55.243ms after Executor acceptance
in v38 and51.484–78.217ms in the three v39 plan programs; artifacts became
ready126.072ms in v38 and132.333–169.462ms in v39. The retained effect
receipts classify viewport pixel change only, so none of these frames is
asserted to be independently verified *useful* task feedback. MAP01 exit
remains false in both runs. Human comparison also has no matched baseline.

This is descriptive analysis of stochastic episodes with different model
actions. A next matched test should instrument actual held-input intervals,
the independently scored first useful outcome and no-control time, then
compare explicit bounded recovery behavior against unauthored coast under
fixed task conditions. The same coverage measure should be transferable to
the desktop and planning benchmarks so an FPS-specific fallback is not
promoted as a general Agent Interface rule.

See [`analysis.json`](results/map01-v38-v39-control-tempo-posthoc-v1/analysis.json),
[`reconstruction source`](analyze_map01_v38_v39_control_tempo_posthoc_v1.py)
and [`cross-OS audit`](audit_map01_v38_v39_control_tempo_posthoc_v1.py).
