# T0 A03 matched-context fixture experiment

This package is a synthetic-method successor to Issue #8341 and preserves the
historical A02 result without editing it. It does not run an agent, model, GUI,
or live interaction; no T1 claim follows from these fixtures.

## Frozen question

Can an independent verifier establish that source-linked current context stays
identical across four history arms and four history depths, that unsupported
queries remain UNKNOWN, and that two literal cue occurrences are distinguished
by exact byte offsets?

## Allocation and isolation

- Allocation: `5947-MULTI-UPDATE-PROVENANCE-T0-A03-20261008`
- Branch: `research/5947-matched-context-t0-a03-20261008`
- Evidence path: `research/analysis/proactive_interference_5947_t0_a03_20261008/`
- Image: `python@sha256:f6a589d43c42b9e7f7dc67a12d37132491f362859a5d750607710cc56da3bc72` (linux/arm64)
- Network: disabled; source read-only; output only in a separate writable mount
- Limits: 1 CPU, 128 MiB memory, no swap, 32 PIDs
- No host fallback is permitted. A failed preflight means STOP.

The corpus has 48 matched rows (3 query conditions × 4 depths × 4 arms) and two
position controls. History slots are fixed at 2,048 bytes. The cue is exactly
seven ASCII bytes. The position controls differ only by offsets 9 and 26.
The auditor is standard-library-only and independently validates raw JSON; it
does not import the candidate.

## Run protocol

Before formal execution, run `python -B -m unittest -v test_t0_a03` in the
pinned container with this source mounted read-only and `/tmp` as the only
additional writable mount. First run candidate exactly once to a new output
directory. If and only if it exits zero and writes nonempty raw JSON, run
auditor exactly once in a separate fresh container invocation. Keep stdout,
stderr, exit codes, raw JSON, and audit JSON immutable. Never rerun either
formal program for this allocation.

Formal execution has not yet been performed. The construction suite is not a
formal result. After formal execution, only read-only hash/readback/index checks
are allowed; do not run tests, import candidate/auditor, or repair this
allocation. Any follow-up requires a new successor allocation.

## H/T/D/C/U

- H (hypothesis): controlled synthetic source-linked current data and UNKNOWN
  behavior can be verified independently despite history variation.
- T (test): 50-row deterministic fixture plus independent exact-byte/schema,
  source-identity, lineage, outcome, and cue-offset audit.
- D (data): frozen candidate JSON, auditor JSON, logs, container identity, and
  SHA-256 manifest; no live/model data.
- C (criteria): construction suite passes all 16 corruptions; candidate exits
  zero once; independent auditor exits zero once with `PASS`, 48 matched rows,
  and 2 position rows. Any deviation is FAIL or STOP.
- U (uncertainty): synthetic method only; no evidence about model behavior,
  latency, user/task effect, GUI, live authority, or real-time control.

## Status

Construction suite passed before freeze. Source was committed and pushed as
`feb8f462599939b239f52dbb0665df020b0de042`; GitHub MCP readback confirmed the
commit tree and all seven blob object IDs. Formal candidate/auditor results and
run hashes will be recorded in `REPORT.md` after the one-shot run.
