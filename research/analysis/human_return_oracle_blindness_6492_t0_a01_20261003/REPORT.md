# Report — #6492 oracle-blind return-cue packets A01

**Status: PASS_METHOD_SCOPED.** The preregistered one-shot candidate and separate raw-only auditor each ran once in the dedicated OrbStack VM. The result is restricted to finite synthetic information-boundary/packet-method validity.

## Lineage

Successor allocation `HUMAN-RETURN-6492-ORACLE-BLINDNESS-A01-20261003-01` targets a specific limitation in #6492 T0: the candidate environment included `pending_step_code` truth labels. Predecessor #6499 and the separate #6520 modal-baseline result remain unchanged and are not pooled or regraded.

## Construction status

The 14-row synthetic fixture separates eight rows in four observational-equivalence pairs from six controls. Public candidate input and auditor-only truth are generated into separate directories. Construction tests exercise candidate output, exact pair invariance, control dispositions, the independent auditor, and eight raw mutation controls. Formal output paths were absent at freeze and were created only for the frozen execution.

Construction suite: 9/9 passed on host Python 3.14.5 arm64. Infrastructure-only probes in the dedicated OrbStack private Engine confirmed public input visibility, auditor truth absence, read-only input/root filesystems, cgroup `memory.max=536870912`, `cpu.max=100000 100000`, and non-root UID 65534 output-mount writes. The input-isolation probe container ID `059110a1583cf7ab0e49e0241c5b54ee487867bae4f72127ac6d4faa12b15893` was recorded. The separate output-mount probe auto-removed successfully, but its container ID was not captured; its stdout/stderr and write sentinel are retained.

## Formal result

The finite preregistered criterion is met.

- Freeze: base/main and merge-base `49cc67de82ed48980245a6e25376bb3ced700a01`; source commit `d1c24af56281ca5cb653f9912171ccb0fdb79d48`; `FROZEN_SHA256SUMS` SHA-256 `40584b6be4ac9f69e822fa897b800b9fe5439fa4179c5149e7f3f9804ff4c27f` (all entries verified before launch).
- Candidate: exactly one invocation, private Engine container `5f2500a3c4c4f2367b982adafd2ac5eac5ebc8398e76874854b01b2cae576768`, exit 0, 2026-10-02 21:34:16 UTC. It had only read-only `/src` and public `/input` mounts and a distinct writable `/out`; no truth/auditor mount. Raw output SHA-256 `aff93afb95ff6d0ee7c78ebbe7ab7db0636679d14833d836e3d0cfc96f1c9919`.
- Auditor: exactly one invocation after candidate exit 0, private Engine container `86afcf97e4709f69d46d2a0132feae72212947cca3b67979ec6184a8d40dfd6f`, exit 0, 2026-10-02 21:34:57 UTC. It received its own auditor source, public fixture, hidden truth and candidate raw output read-only; it did not receive candidate source. Audit output SHA-256 `ce04e14247b312399027c420008112b6c63d98dc795b407bd2742a2cbb7e32f5` reports `PASS_METHOD_SCOPED`, 14 rows, four equivalence pairs, zero errors.
- Both used image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`linux/arm64`), no network, one CPU, 512 MiB, UID 65534, read-only root, all capabilities dropped, and no-new-privileges. Captured Docker inspect metadata confirms each mount and effective configuration. Stdout/stderr, exit statuses, container IDs and raw JSON are retained under `results/formal-01/`.
- Formal counts: candidate 1, auditor 1, retries 0. Construction suite remained 9/9; its eight mutation controls were rejected in construction tests, not treated as extra formal candidate/auditor invocations.

This result does not establish human comprehension, usefulness, return-to-work benefit, safety, UI validity, privacy acceptability, or product behavior; it does not authorize T1.

## Local integration checks

- `python3 research/analysis/check_index.py`: PASS before and after integration merge (590 then 593 retained result/failure directories indexed).
- `python -m unittest discover -s research -p 'test_*workspace*.py' -v`: PASS, 21 tests; `python research/check_workspace_index.py --git-tree`: PASS, 156 top-level research directories reachable.
- This package's construction suite: PASS, 9/9. The analysis-index workflow's other local unittest groups and the two #6492 predecessor allocation suites passed when invoked from their declared working directories.
- A naive local replay of the entire analysis-index workflow is not a faithful CI invocation: it omits the workflow's first step, which restores the frozen workflow file from commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd`. Consequently, two unrelated #6590 provenance tests compare the current later workflow hash against the frozen hash and fail in that naive replay. The package itself and index checks pass; hosted PR CI must still confirm the workflow-native restored-source path.
- `git diff --check`: PASS. Formal execution result files and their `results/formal-01/SHA256SUMS` all verify.

## Scope boundary

This is synthetic method validation only. It cannot establish human comprehension, return-to-work benefit, safety, UI validity, privacy acceptability, or product behavior.
