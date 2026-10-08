# Construction record

Non-formal local Docker construction work only; these checks are not formal allocation rows.

- RED: the safety-stop test rejected a `DEFERRED_SAFETY` heterogeneous session row that also claimed `total_cost=8`. That total could be read as a completed-task comparison despite the warning gate. Candidate was changed to report `incurred_cost=8` only; the independent formal auditor also rejects any completed total for that row.
- GREEN: `python -m unittest -v test_probe` — 5 tests passed, 0 failures, in the final pre-freeze construction run.
- Controls tested: repeated-family cost ordering, critical-warning refusal before consequential input, partial restoration remains UNKNOWN, competing generation change refuses stale input, and callback collateral is not described as restored.
- Candidate construction output is under `construction/formal.json`; it declares `construction_invocations=1` and `formal_invocations=0`. It is not the formal outcome.
- An earlier pre-mode test scaffold emitted `out/formal.json` before the formal/construction flag was added. It was moved unchanged to `construction/pre_mode_candidate_raw.json`; its embedded formal counter is a harness-labeling defect, not a formal invocation. It is retained but excluded from every scientific tally.
- Formal source freeze followed these checks. Formal candidate and auditor are each intended to run once; no post-freeze repair or retry is allowed.
