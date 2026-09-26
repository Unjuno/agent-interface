# Issue #3885 — matched causal task-effect contract, R4

## H — hypothesis

For deterministic matched fixtures, a candidate task effect is attributable to
one actuation only when pair/state/seed/schedule/scorer/window identities match,
determinism is attested, the candidate arm differs by one actuation, baseline
task input is zero, the candidate ledger is valid, clocks are comparable, an
independently scored candidate effect is present inside the window, and the same
effect is absent from the baseline. Otherwise the result is `UNRESOLVED`.

## T — test

The candidate and independent oracle enumerate all 15 Boolean gates and both
useful/harmful polarities: exactly 65,536 rows. Construction checks exercise
positive polarity separation and each single-gate corruption but allocate zero
formal rows. The formal invocation writes its complete JSONL truth table once.
The auditor is a third implementation and independently re-derives every row,
checks complete unique coverage, authority=false, and directed laundering cases.

Run only inside the pinned linux/arm64 OrbStack image, with `--network none`,
read-only container root, and the experiment directory mounted as `/src` (read
only) plus the dedicated result directory mounted at `/out` (read/write).
No game, model, GUI, X11, ViZDoom, gameplay input, or shared runtime is used.

## D — data

The frozen candidate, oracle, construction checks, formal runner, audit, and
base snapshot are identified in `FREEZE.json`. The one formal output is under
`results/formal-01/`, containing all rows and its result summary. Container
stdout/stderr, independent audit output, and post-run hashes are retained next
to the output.

## C — criteria

PASS requires 65,536 unique rows, zero candidate/oracle/auditor disagreement,
exactly one useful and one harmful causal disposition, all other rows unresolved,
zero authority grants, all 30 polarity-specific single-gate corruptions and
three extra laundering controls unresolved, one formal invocation, and intact
source/result hashes. A missed gate causing causal promotion is FAIL; semantic
disagreement is FAIL; any hash or source-snapshot discrepancy is HOLD_INTEGRITY.

## U — scope limits

This finite deterministic-fixture contract does not prove stochastic MAP01
replay, broad gameplay utility, recovery efficacy, survival, latency, tokens,
human tempo, or product readiness. It grants no live allocation or input/model
authority.

## Predecessor integrity finding

The source bundle committed for #1873 does not match its own manifest. The
manifest declares 3,680 base64 bytes and per-file sizes 709/1,741/832/888/4,399;
the committed bundle is 5,424 bytes and expands to 724/2,871/3,577/3,284/4,797.
`restore_source.py` stops at its length/hash assertion. R4 does not alter those
bytes and instead freezes a fresh independent implementation from the #1873
Issue contract.
