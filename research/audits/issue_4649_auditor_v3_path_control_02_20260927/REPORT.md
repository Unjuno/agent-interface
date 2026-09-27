# Issue #4649 — auditor-v3 path-confinement controls, allocation 02

## Disposition

**PASS_PATH_CONFINEMENT_V3** for this finite synthetic controls-only allocation. An independent Docker auditor verified the result, frozen inputs, and all five case outcomes with `errors=[]`.

This is a new allocation with a corrected probe gate, not a retry or rewrite of allocation 01. Allocation 01's `FAIL_PATH_CONFINEMENT_OR_COMPATIBILITY`, raw result, and invocation record remain unchanged. The correction changes the control harness to require the expected rejection marker as a member of the error list while allowing additional independent ledger diagnostics, as stated in the original plan.

## H / T / D / C / U

- **H:** Resolving input paths and requiring the resolved target to stay beneath the canonical input root rejects traversal and symlink escapes while preserving ordinary files and in-root symlinks.
- **T:** One separately frozen Docker invocation ran the byte-identical candidate `audit_v3.py` from allocation 01 with the corrected probe. Five synthetic cases were evaluated. A v1 PASS stub isolated v3 ledger/path behavior. Formal #4649 runner and prior eight-control harness invocations were 0.
- **D:** **PASS_PATH_CONFINEMENT_V3**, probe exit 0. Contained file and in-root symlink both returned `PASS_INDEPENDENT` with empty errors. Literal `../outside/sentinel`, input symlink to a sibling file outside the root, and manifest symlink outside the root each returned structured `FAIL`, with the required path error marker and empty stderr. All five gates passed. A separate independent Docker auditor returned `PASS_INDEPENDENT_AUDIT_OF_SCOPED_PASS`, errors `[]`.
- **C:** Candidate source SHA-256 `7b506919f5ed0a9b6c1fe2ebd4a720ed4c2b41bf38ed8d9c6939e2fc9685863d`; corrected probe SHA-256 is recorded in `FREEZE.json`. Candidate is based on the exact #4672 v2 source SHA-256 `500946223763825cd7773dacae55ab67cc3b624b958c941fdd84b2b877f73630`, included under `base_v2/`. Docker Desktop 28.5.1; cached image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, CPython 3.12.14; network none, pull never, read-only root/source, 1 CPU, 256 MiB, 32 PIDs, 32 MiB noexec/nosuid tmpfs.
- **U:** Synthetic ledger/path controls only; v1 is stubbed. No combined v1+v3 audit, formal01 rerun, previous eight-control validation, concurrent filesystem mutation/TOCTOU test, or production claim. The earlier #4649 and allocation-01 failure dispositions remain intact.

## Reproduction

With the pinned image cached, from a clean checkout:

```sh
out="$(mktemp -d)"
docker run --rm --pull=never --network none --cpus=1 --memory=256m --pids-limit=32 --read-only \
  -e EXPECTED_IMAGE_ID=sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  -v "$PWD/research/audits/issue_4649_auditor_v3_path_control_02_20260927:/study:ro" \
  -v "$PWD/research/audits/issue_4649_auditor_v3_path_control_02_20260927/probe_v3_gatefix.py:/probe_v3.py:ro" \
  -v "$out:/out:rw" --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python -B /probe_v3.py
```

The expected exit is 0 with `PASS_PATH_CONFINEMENT_V3`. The retained formal01 raw result is never overwritten by this fresh-output command.

Allocation 01 remains documented at `research/audits/issue_4649_auditor_v3_path_control_20260927/`; the original v2 finding remains in PR #4681. This additive allocation closes neither #4649 nor its broader evidence questions.
