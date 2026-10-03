# Begin-to-receipt causality boundary — #5215

A matching execution receipt can report a start before its accepted `begin_execution()` call.
The pinned kernel does not retain that admission timestamp. Its `record_execution()` method checks identity, count and release evidence, then advances to EXECUTED without this causal comparison.
This package preserves a new ordinary engineering characterization and one isolated candidate.
It changes no `runtime/kernel` file and does not retry or adjudicate the historical #5216 experiment.

Pinned source: main `3116528f3abe0fec72cfc1b5b2b5b4b05538512e`, with exact Git bytes of the four kernel modules in `frozen_kernel/` and their blob/SHA-256 identities in `SOURCE.json`.
The prospective [plan](PLAN.md) and `FREEZE.json` define the scope and complete 432-row denominator.
The candidate remembers the timestamp only after a successful begin and rejects receipt starts strictly below it, before delegating the original identity/state checks.
Equality and later start/end/release times remain representable.

| Ordinary check | Observed result |
|---|---|
| Test-first baseline | 6 tests; 2 expected failures; exit 1 |
| Isolated candidate, normal / `-O` | 6/6 each; exit 0 |
| Unmodified current-main kernel suite | 18/18; exit 0 |
| Baseline matrix | 216 rows; 108 accepted, including 60 pre-begin starts |
| Candidate matrix | 216 rows; 48 accepted, zero pre-begin starts |
| Independent raw-only oracle | 432 unique rows reconstructed, no errors |
| Copied-data corruptions | 20/20 return HOLD, 2 test methods pass |
| Implementation mutations | All four cause test refusal/failure; original wrapper exit 1 retained |
| Compilation | exit 0 |

Manifest mismatches are refused in both arms. Every refused matrix row leaves the request intact, execution absent and stage AUTHORIZED.
The 60 earlier matching starts account for the entire acceptance difference; the remaining 48 matching equal/later rows are preserved.
The auditor imports no kernel, producer, fixture or candidate. It requires exact schemas/types, complete unique coverage, provenance and independently derived acceptance/state outcomes.

## Mutation wrapper limitation

The first implementation-mutation wrapper incorrectly required a unittest `failures=` summary.
Equality refusal and premature timestamp storage instead cause expected `ContractError` entries counted as `errors=`.
The wrapper therefore exited 1 even though all four mutants were detected.
Its first command/log/result are retained unchanged. `mutation-adjudication.json` reads those existing logs/sources and confirms semantic failures, excluding import/setup errors; no mutant execution was repeated.
Sanitized logs and exact mutant source bytes are in `evidence/mutations/`.

## Reproduction and provenance

From repository root, in PowerShell:

```powershell
$env:BEGIN_CAUSALITY_ARM = 'candidate'
python -m unittest discover -s runtime/results/kernel-begin-causality-01a0ff58 -p test_boundary.py -v
python -O -m unittest discover -s runtime/results/kernel-begin-causality-01a0ff58 -p test_boundary.py -v
Remove-Item Env:BEGIN_CAUSALITY_ARM
python -m unittest discover -s runtime/results/kernel-begin-causality-01a0ff58 -p test_audit.py -v
python -m unittest runtime.kernel.test_kernel -v
```

On POSIX use `BEGIN_CAUSALITY_ARM=candidate` as the environment prefix for the two boundary commands.
With the variable absent, boundary tests intentionally reproduce the baseline's two failures.
For a fresh **ordinary** matrix replay, choose two unused output paths:

```text
python runtime/results/kernel-begin-causality-01a0ff58/probe.py NEW_RAW.json
python runtime/results/kernel-begin-causality-01a0ff58/audit.py NEW_RAW.json NEW_AUDIT.json
```

Commands, actual UTC begin/end and runner exits are retained in `evidence/*.command.json`.
Candidate unit-test environment selections are in `evidence/command-environment.json`.
The raw record identifies Windows and CPython 3.11.9. These are authored integer records, not physical clock measurements or performance samples.
Private original logs remain in the worker's private output area; public logs redact only local path prefixes and retain their original/public hashes.
The two external harness source snapshots are retained as nonexecuting `.txt` evidence.
`SHA256SUMS` binds public bytes; frozen input source hashes remain separately fixed.

## Variables and limits

| Symbol/field | 日本語の意味・定義 | SI unit | Range / assumption | Type |
|---|---|---|---|---|
| begin_ns | 受理済みの実行開始呼出し時刻 | s, stored as ns (10^-9 s) | 1..4 in one synthetic comparable clock | exact int |
| started_ns | 実行受領書が主張する開始時刻 | s, stored as ns | 0..5, same clock | exact int |
| ended_ns | 実行受領書が主張する終了時刻 | s, stored as ns | started_ns..6 in matrix; 20 in late-completion control | exact int |
| manifest_matches | 受領書と要求のmanifest IDが同一か | dimensionless | false/true | bool |
| accepted | lifecycleが受領書を受理したか | dimensionless | false/true, actual observed API result | bool |

The scoped decision is `PASS_SCOPED_ENGINEERING` for this isolated lower-bound candidate.
No scientific, runtime promotion, application-effect, performance or product PASS follows.
Assumptions: sequential execution, one accepted begin per lifecycle, and trusted comparable timestamps.
This does not prove clock alignment, physical release, last-action/lease cutoff, effect causality, concurrent safety or public MCP behavior.
#6852's duplicate-begin fix, #6855's release lower bound and #6864's cancellation-release boundary are separately owned.
A future runtime adoption must coordinate their state/ownership contracts and independently validate the composed tree.

No backend, GUI, input, container, GPU, model or formal allocation was used.
The candidate is not imported by runtime/kernel and no workflow points to this package.
The inspected kernel workflow runs the existing explicit module; this evidence path is not its automatic discovery target.
Main's kernel dependency blobs were rechecked unchanged at `f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549` after the matrix.
Main publication remains a separate FINAL-v5 nonauthor-review and conditional-application gate.
