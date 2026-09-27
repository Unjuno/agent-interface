# Issue #4649 — auditor-v2 symlink confinement control

## H / T / D / C / U

- **H:** Auditor v2's lexical `..` path guard may reject traversal strings but still follow a symlink from the input root to a file outside that root. A focused Docker control using a pinned, self-consistent synthetic manifest will establish whether the wrapper detects that boundary escape.
- **T:** Invoke only the exact `audit_v2.py` from PR #4672 against synthetic disposable files. Supply a stub v1 auditor that returns a valid PASS envelope so this allocation isolates v2's ledger/path check; it does not represent the combined v1+v2 audit. Run two controls once: literal `../` traversal and a safe-looking relative path that is a symlink to a sibling file outside the input root. Do not invoke the #4649 formal runner or prior eight-control harness.
- **D:** Scoped PASS iff both path attacks produce structured FAIL and nonempty errors, with empty stderr. Any symlink-escaped file accepted as `PASS_INDEPENDENT` is `FAIL_SYMLINK_PATH_CONFINEMENT`; an execution/source identity mismatch is STOP. Preserve raw JSON, stdout/stderr, exit, and exact hashes. No retry.
- **C:** Docker Desktop local daemon; cached image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64. Network disabled, image pull disabled, read-only root/source mount, disposable writable output mount, bounded CPU/memory/PIDs. PR #4672 head is `0b7b3ceb70176da1e1a9f73d3cf228be280472ec`; v2 source is checked against SHA-256 `500946223763825cd7773dacae55ab67cc3b624b958c941fdd84b2b877f73630` before execution.
- **U:** This is a synthetic unit-level confinement characterization of `ledger_errors`, with v1 intentionally stubbed. It does not validate the eight prior corruption controls, formal01 result, v1 behavior, repository-wide path policy, or production exposure. A failure is a scoped auditor robustness finding, not evidence that the preserved #4649 raw result changed.

Allocation: `issue4649-auditor-v2-symlink-confinement-20260927-01`.
