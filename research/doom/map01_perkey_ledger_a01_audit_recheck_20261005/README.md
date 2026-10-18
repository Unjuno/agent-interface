# Per-key ledger A01 raw-audit recheck

## H / T / D / C / U

**H:** The predecessor A01 raw-only auditor can accept stale candidate interval output after a raw timestamp mutation because it checks a hard-coded `70..90 ns` interval instead of deriving the bounds from raw events.

**T:** Using byte-identical raw and candidate output from PR #7701 head `9ec46a5782257f6e47b6bd4cc28c5bdb1babd58f`, I ran the original auditor against a temporary raw copy with only W's `release_sync_ns` and `up_sample_ns` increased by 1 ns. I then ran the additive independent auditor on the untouched pair and on the mutated raw with stale output. Four mutation tests also checked a corrected `91 ns` output control.

**D / result:** `PASS_AUDIT_MUTATION_SENSITIVITY`. The frozen auditor returned 0 and `PASS` for the mutated raw with unchanged output. Its raw-derived W upper bound should be 91 ns, while the unchanged candidate output says 90 ns. The corrected auditor passed the original pair (exit 0), rejected mutated raw with stale output (exit 1), and reconstructed upper bound 91 ns. All four tests pass. No candidate invocation or live allocation was added.

**C:** This establishes audit mutation sensitivity for one deterministic synthetic fixture. It improves the integrity of the arithmetic evidence in PR #7701; it does not establish physical key-up timing.

**U:** No game, GUI, model, OS input, physical release, useful feedback, bounded recovery, task effect, survival, or MAP01 outcome was tested. The live #59 allocation remains separately gated and unassigned.

## Reproduction

From this directory:

```sh
python3 -B -m unittest -v test_audit_recheck.py
python3 -B run_recheck.py
```

`inputs/` contains byte-identical copies of the predecessor audit, candidate, ledger, raw fixture, and candidate output. Their digests and the recheck source digests are in `FREEZE.json`. `results/` preserves the baseline false pass, corrected pass/fail reports, mutated raw fixture, commands' stdout/stderr/exit records, and the test output. `results/preflight-hash-check-error.txt` records two early verification-command path mistakes; the corrected frozen hash check passed before the recorded test and recheck runs.

The candidate was not rerun. The parent A01 package, its raw result, and its original manifest remain unchanged in the predecessor PR branch.
