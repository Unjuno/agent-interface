# Issue #4649 — ledger-bound auditor v2 controls, allocation 02

## Disposition

**PASS_LEDGER_BOUND_AUDIT_CONTROL_SCOPED.** In the separately frozen local-Docker controls allocation, the untouched formal01 result passed both v1 raw reconstruction and the v2 input-ledger binding check. All 8/8 copied-result corruption controls were rejected with exit 1, structured errors, and empty stderr. The two v1 false-PASS cases (`drop_input_row`, `input_digest`) were rejected with `V2_REPORTED_INPUT_LEDGER_MISMATCH`.

This does not change formal01's overall **FAIL_AUDITOR_ROBUSTNESS** disposition, and the formal runner was not invoked. A preceding exploratory pilot lacked an ex-ante source hash; it is retained as `HOLD_PRE_FREEZE_SOURCE_HASH_MISSING`, not counted as formal evidence. Allocation 02 is the frozen confirmation.

## Frozen identity and execution

- Allocation: `issue4649-auditor-ledger-v2-20260927-02`; Issue #4649.
- Intake main: `51263d3997e860d01fbe7387104dbf211bfcde10`.
- Allocation plan blob: `bd90f9d1e33b080644b5ab9c43a1f8df950c56e6`; source blob: `1d570ffaa8b0cab1b1dd806d4b99eee1232b22d3`. The v1 auditor and control harness are frozen in predecessor branch/PR #4659; their hashes are listed below and that additive-source PR remains a separate integration dependency.
- v2 source SHA-256: `500946223763825cd7773dacae55ab67cc3b624b958c941fdd84b2b877f73630`; allocation freeze SHA-256: `5ff753fd82eb15a1220b8021afe2f1e3569233be34ab2530a67bb96067a6fd2d`.
- Formal01 input artifacts remained pinned: manifest `8180a34bb58ca94ac2734baba0cc84e6316144f37ffac7bb5977d2d6927e7438`, predecessor freeze `4665fbf32c86d66dcea3c6efdd6b073c39486321fae48ec8f07104de325b2a9f`, formal result `aa7de87e5cf0644eb5bbe645d34d9273a8fbefccf041faea12b4e6933886f6b7`, v1 auditor `dc12e14860296b0d8900aaa66d1465101a0fcd7d4ede69d0b24dd775ad5fee66`, controls harness `5893bb46ac503943cd0b2d329a18f8dca2267a83b345e82059b5b3103dcb1938`.
- Local Docker Desktop 29.8.0; cached image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; Linux/amd64, CPython 3.12.14. `--pull=never --network none --cpus=1 --memory=1g --pids-limit=64 --read-only`, 64 MiB noexec/nosuid tmpfs, readonly study/input/result/source, dedicated writable output.
- No formal runner, network, workflow/Actions, remote runner, package install, model, GUI, or OS input.

## Result details

Untouched baseline: v1 `PASS_INDEPENDENT`, v2 `PASS_INDEPENDENT`, errors `[]`, stderr empty, exit 0. The separately executed unchanged v1 control harness generated 8 rows; each was structurally rejected (exit 1, nonempty auditor errors, empty stderr). The v2 output auditor independently rechecked the baseline and every row: 8 checks passed. Raw row-level details are in `results/formal01/CONTROLS.json`; separate audit summary is `results/formal01/INDEPENDENT_AUDIT.json`.

The correction is a full equality check between the candidate result's `input_sha256` object and the independently recomputed manifest path+digest table, in addition to checking those bytes against the separately frozen hashes. No v1 source or formal01 artifact was changed.

## Retained hashes

| Artifact | SHA-256 |
|---|---|
| Baseline stdout | `8b6be6c0789bfd2539ee04b3e33f362859c5934083be41f468374b5d6cd5026f` |
| Baseline stderr (empty) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Baseline exit record | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `CONTROLS.json` | `9b333af0f846ef2f451fe9c590e8c1ed293696722fa45d2a9aaf646789b8602a` |
| `INDEPENDENT_AUDIT.json` | `d7aa14658a5b555902f8aeca01dc84904c22fca448180e0d8e3fbddd445b7bae` |
| Controls stdout | `1086c82d64b232210602b0d0f8a70740c720837392fea1658ab17f562ba49528` |
| Controls stderr (empty) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Controls exit record | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |

## Scope

This is a finite copied-result integrity-control PASS over synthetic retained inputs on local linux/amd64 CPython 3.12.14. It is not a rerun of the byte-delivery formal experiment, an ARM64 reproduction, a production reliability result, or a product claim. The earlier v1 overall failure stays visible and unchanged.
