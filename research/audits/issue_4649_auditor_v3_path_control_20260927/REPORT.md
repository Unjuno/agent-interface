# Issue #4649 — auditor-v3 resolved-path confinement controls

## Disposition

The frozen allocation's official gate remains **FAIL_PATH_CONFINEMENT_OR_COMPATIBILITY**. The failure was preserved; no retry or relabel occurred. A separate Docker audit of the retained rows found that all three escape controls were rejected and both in-root controls passed. It also identified why the frozen probe's aggregate gate was false: the probe required the input-symlink error list to equal exactly `["V3_UNSAFE_INPUT_PATH:sentinel"]`, while the auditor correctly also reported input-ledger key-set and result-ledger mismatches. The preregistered plan required the expected V3 error, not exclusivity of the whole error list. This is a control-harness implementation defect; posthoc evidence does not replace or upgrade the original gate.

## H / T / D / C / U

- **H:** Resolving input paths and checking that each resolved path remains beneath the canonical input root will reject outside-root symlink escapes while allowing ordinary files and in-root symlinks.
- **T:** One local Docker allocation ran the additive `audit_v3.py` against five synthetic disposable cases. The v1 auditor was intentionally stubbed PASS to isolate ledger/path behavior. Formal #4649 runner and previous eight-control harness invocations: 0.
- **D:** Observed rows: contained regular file `PASS_INDEPENDENT`; contained symlink `PASS_INDEPENDENT`; `../outside/sentinel` structured `FAIL`; input symlink to sibling file structured `FAIL` with `V3_UNSAFE_INPUT_PATH:sentinel`; manifest symlink to sibling file structured `FAIL` with `V3_UNSAFE_MANIFEST_PATH`. All stderr fields were empty. The probe's preregistered gate nevertheless returned `FAIL_PATH_CONFINEMENT_OR_COMPATIBILITY` / exit 1 because it used exact-list equality for one expected error list. Independent posthoc audit: `PASS_INDEPENDENT_AUDIT_OF_RETAINED_GATE_FAIL`, errors `[]`.
- **C:** Candidate source `audit_v3.py` SHA-256 `7b506919f5ed0a9b6c1fe2ebd4a720ed4c2b41bf38ed8d9c6939e2fc9685863d`; based on the byte-identical #4672 v2 source SHA-256 `500946223763825cd7773dacae55ab67cc3b624b958c941fdd84b2b877f73630`, also retained as `base_v2/audit_v2.py`. Docker Desktop 28.5.1, pinned cached image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, CPython 3.12.14; network none, pull never, read-only root/source, 1 CPU, 256 MiB, 32 PIDs, 32 MiB noexec/nosuid tmpfs. Raw output, invocation receipt, freeze, and independent audit are retained.
- **U:** Synthetic controls only. The v1 stub means this does not validate the combined v1+v3 audit, prior eight controls, original formal01 bytes, or production behavior. It does not test concurrent filesystem mutation/TOCTOU; containment assumes the read-only input tree stays stable during this bounded audit. The official gate remains FAIL pending a separately frozen harness-corrected allocation.

## Reproduction

With the cached image available, a clean checkout can run the frozen probe once using a new output directory:

```sh
out="$(mktemp -d)"
docker run --rm --pull=never --network none --cpus=1 --memory=256m --pids-limit=32 --read-only \
  -e EXPECTED_IMAGE_ID=sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  -v "$PWD/research/audits/issue_4649_auditor_v3_path_control_20260927:/study:ro" \
  -v "$PWD/research/audits/issue_4649_auditor_v3_path_control_20260927/probe_v3.py:/probe_v3.py:ro" \
  -v "$out:/out:rw" --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python -B /probe_v3.py
```

The command is expected to return exit 1 with the exact raw disposition above. The independent auditor is a separate one-shot Docker command that reads the retained `results/formal01/RESULT.json` and writes `results/independent_audit/INDEPENDENT_AUDIT.json` to a fresh output directory.

The exact v2 predecessor remains at #4672; #4681 retains the original v2 symlink-acceptance finding. This v3 candidate and its gate failure are additive and do not alter either result or close #4649.
