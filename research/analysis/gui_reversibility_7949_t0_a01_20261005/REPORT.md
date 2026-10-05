# Result — T0 A01

Disposition: **PASS_METHOD_SCOPED** for the fixed finite model. The candidate
and independently written exhaustive sequence oracle agree on all six cases;
the candidate matches every predeclared label. This is an analytical method
result with a Windows-host substitution because WSLc did not return from its
image/container inspection and pull commands. No candidate command ran in
WSLc, and no isolation or resource-limit claim is made.

The fixed candidate command was `python -B run_candidate.py` from this package
directory on Windows 10 build 26200.9550 with Python 3.12.10. The frozen source
and input SHA-256 values are recorded in `FREEZE.json`. Candidate raw output is
`raw/candidate.stdout.json`; independent oracle and audit output is
`raw/audit.json`. The audit verifies the candidate raw SHA-256
`710faaff22ed2731b9c388f2e1d0e59e6a5bd10f3640d6eaf045ab12d250a739`, all six
labels, and two fail-closed mutation controls.

The uniform positive had two common two-operation recovery sequences. The
branching positive was recoverable only with a receipt-conditioned one-operation
choice. The partial case contained outcome `001` with no path to target `000`;
the static `reversible=true` baseline incorrectly called it
`UNIVERSALLY_UNIFORM`. Indistinguishable outcomes needing different operations,
incomplete coverage and an invalidated receipt all classified `UNKNOWN`.
The independent oracle enumerated 63 start/sequence traces in the complete,
fresh cases.

The case called `external_write` tests only that a supplied invalidated-receipt
flag forces `UNKNOWN`. It does not model or detect the external write event or
its write-state transition. Similarly, `coverage_complete=false` checks
fail-closed handling of an uncertified coverage flag rather than discovering
an omitted outcome. Those flags are assumed inputs. A next empirical transfer
would need independently witnessed application outcomes and effect receipts;
this result does not justify runtime admission or any GUI safety claim.

## Reproduction

From this directory, the one-time fixed candidate command is:

```powershell
python -B run_candidate.py
```

After retaining that output, the independent audit command is:

```powershell
python -B audit.py
```

The audit writes `raw/audit.json`. Do not rerun the fixed candidate under the
same run ID or overwrite either raw file.
