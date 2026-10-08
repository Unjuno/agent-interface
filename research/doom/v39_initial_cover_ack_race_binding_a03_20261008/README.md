# Initial-cover ACK and final-empty race A03

## H / T / D / C / U

**H.** The exact current-main drain can return sequence 11 while sequence 12 is queued just after its final empty check. The latest candidate adds a wrapper intended to bind the initial cover's submitted sequence before waiting for its ACK, then recover a stale rejection from the queued full observation and discard the old cover.

**T.** Freeze current main `1f81daa690b567a9a049cc75fae8619b2660c343` and candidate PR #8643 head `6671acd1395238f3b0805e6cbe03aea12da028bf`. Reproduce the queue interleaving with the exact baseline drain. Invoke the exact candidate `submit_initial_cover_with_recovery` wrapper while sequence 12 remains queued and the submitted source remains sequence 11. Verify recovered sequence, hard-crossing monitor result, discarded cover disposition, and no retry.

**D.** PASS only if the baseline misses sequence 12, the wrapper records submitted sequence 11 before ACK handling, candidate recovery returns and evaluates sequence 12, discards the old cover, and consumes the queued event without resubmission. Otherwise FAIL or HOLD on source mismatch.

**C.** This deterministically tests the boundary between source selection, submit ACK handling and the bounded recovery helper. It does not estimate how often the schedule occurs. The monitor is a narrow test double; the candidate wrapper and recovery functions are exact source extracts.

**U.** No full controller process, production monitor, App Server, model, game, GUI, OS input, physical release measurement, or task effect is run. The result establishes helper/wrapper behavior plus static `main` wiring for this schedule only. Issue #59's live exposure and integrated task-effect gates remain open.

## Result

The baseline drain returned 11 with `pending_events=false` and sequence 12 queued. The candidate wrapper bound submitted sequence 11, recovered sequence 12 after stale rejection, evaluated its hard crossing, discarded the old cover until a fresh plan, and consumed the queued event without retrying the cover.

Frozen source identities are in `FREEZE.json`; raw output, result, audit and checksums are retained as `RUN.stdout.txt`, `RESULT.json`, `AUDIT.stdout.txt` and `SHA256SUMS.txt`.

## Reproduction

```powershell
py -3.13 -B research/doom/v39_initial_cover_ack_race_binding_a03_20261008/run_experiment.py
py -3.13 -B research/doom/v39_initial_cover_ack_race_binding_a03_20261008/audit.py
py -3.13 -B -m unittest discover -s research/doom/v39_initial_cover_ack_race_binding_a03_20261008 -p test_ack_binding.py -v
```

This is a source-bound construction, not a live threat exposure or integrated product result.
