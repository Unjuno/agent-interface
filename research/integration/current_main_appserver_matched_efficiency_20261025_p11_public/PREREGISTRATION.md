# P11 preregistration — corrected-runtime matched caller comparison

Frozen at the recorded current-main commit before any provider generation. P09 remains immutable and incomplete because raw ledger bytes were changed by its redactor. P10 p01-direct is separately retained as a pre-provider runtime setup failure (Python 3.11 unsupported by the bounded Windows pipe client); it is not replaced or included in this comparison. P11 uses preinstalled CPython 3.13.14 for every cell.

P11 has six one-shot arms in counterbalanced order: direct/compiled, compiled/direct, direct/compiled. Each arm uses one new Fake X session, one exact public observation image, one `gpt-6.1-sol` low-effort turn, one mint, and one route-specific public action. Retries and recovery are zero. No model call begins until package tests and a no-generation App Server initialize/close preflight pass.

A pass requires protocol/provider/ledger usage agreement, exact image provenance, selected point in the green target, same-sequence mint, exactly one owner click/effect, expected final pixel, verified release, complete ledger, and unchanged raw response hashes after redaction. Any failure or unknown remains retained and counts as a non-pass. Do not replace a cell.

Report all six cells, per-arm counts and paired timing/token deltas. Three pairs are exploratory descriptive evidence only. No WSLc, Docker, physical input, live application, MAP01, blocked-I/O recovery, or broad reliability conclusion follows.
