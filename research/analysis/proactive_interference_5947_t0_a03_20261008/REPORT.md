# A03 report

Disposition: `PASS_FIXTURE_METHOD_SCOPED`.

The single formal candidate invocation exited 0 and wrote 50 rows. The single
separate raw-only auditor invocation exited 0 and returned `PASS`, 48 matched
rows, 2 position rows and no errors. Formal outputs and stdout/stderr are
retained under `formal/`; construction checks and formal result are distinct.

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

## Formal one-shot result

- Candidate: exactly one invocation, exit 0; stdout reports allocation and 50
  rows; stderr empty. Raw file size 507,339 bytes.
- Auditor: exactly one invocation in a separate fresh container, exit 0;
  `{"errors":[],"matched_rows":48,"position_rows":2,"result":"PASS"}`;
  stderr empty. No candidate/auditor reruns, imports, or post-run tests.
- Commands: `python -B candidate.py /out/candidate.json`; then, in a separate
  container invocation, `python -B auditor.py /out/candidate.json /out/audit.json`.
- Both runs used the pinned image, network disabled, read-only source, separate
  writable `/out`, 1 CPU, 128 MiB, no swap, 32 PIDs. Preflight enforcement:
  `memory.max=134217728`, `memory.swap.max=0`, `cpu.max=100000 100000`,
  `pids.max=32`.
- Raw SHA-256: `43f0d3ec7171b96de56fdbf8e7b411ee957764c919d7a02dc966865f6d3d3cef`
- Audit SHA-256: `6727564a6b867e659e187f88e17acf9521f07d5eab9a720a2a68c0229bc7ffa1`
- Candidate stdout SHA-256:
  `75e640891f42aef458ae175b9b5579556b269fd331009bc57c05876a2c78aef1`
- Auditor stdout SHA-256 equals audit JSON:
  `6727564a6b867e659e187f88e17acf9521f07d5eab9a720a2a68c0229bc7ffa1`
- Both stderr files are empty (SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
- The construction mutation gate rejected all 16 controls. This is a scoped
  fixture/auditor integrity result, not a model behavior result.

## Frozen source

- Main/base SHA: `d4ac01bcb8bfc3a9eb13c8b00f43cb3ef02eccac`
- Frozen commit: `feb8f462599939b239f52dbb0665df020b0de042`
- Freeze-record commit: `480e44c1a334416a4a309a2c59ffc25f153968a4`
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
- D: `PASS_FIXTURE_METHOD_SCOPED`; exact one-shot output and hashes retained.
- C: gate met: candidate once, then auditor once, PASS/48/2 with zero errors.
- U: no live/model/task/latency/GUI/generalization inference.

## Scope limits

Only the deterministic synthetic corpus and its independent verifier were
validated. No model/tokenizer, agent, human, GUI, application, task-effect,
latency, adaptation, safety, deployment, or generalization claim is supported.
Issue #8353 remains open; no T1/live authority is implied.
