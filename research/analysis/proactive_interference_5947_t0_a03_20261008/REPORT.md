# A03 report

Status: construction checks complete; immutable freeze verified; formal run
not yet started.

## Construction evidence

Pinned network-disabled container, read-only source and isolated writable temp:

- `python -B -m unittest -v test_t0_a03`
- Result: PASS, 3 test methods; 16 independent corruption mutations rejected;
  valid corpus accepted; candidate and auditor overwrite refusals checked.
- An initial test attempt with a fully read-only container had no writable
  temporary directory and stopped before tests executed. No repository files
  were written by that attempt. The test was rerun with `/tmp` as the only
  writable mount and passed.

This is construction evidence, not the formal candidate/auditor result.
Formal run outputs, exit codes, raw and audit hashes, and exact container
settings will be appended after the one-shot execution.

## Frozen source

- Main/base SHA: `d4ac01bcb8bfc3a9eb13c8b00f43cb3ef02eccac`
- Frozen commit: `feb8f462599939b239f52dbb0665df020b0de042`
- Branch: `research/5947-matched-context-t0-a03-20261008`
- Tree: `c917c4e197d210fbf7d19316496103126a49a327`
- GitHub MCP confirmed the commit tree and read back each of the seven file
  blobs by ref; their Git object IDs matched the frozen tree.
- Container preflight: `memory.max=134217728`, `memory.swap.max=0`,
  `cpu.max=100000 100000`, `pids.max=32`; source read-only and isolated
  writable `/tmp`; network disabled.

## H/T/D/C/U

- H: see package README; current-source-grounded answers and UNKNOWN remain
  invariant across matched history arms.
- T: 48 matched synthetic rows plus two byte-offset controls; independent
  exact-schema and exact-byte auditor.
- D: synthetic only; formal outputs pending.
- C: candidate once, followed by auditor once only after candidate success;
  auditor must report PASS/48/2. Otherwise preserve FAIL/STOP.
- U: no live/model/task/latency/GUI/generalization inference.
