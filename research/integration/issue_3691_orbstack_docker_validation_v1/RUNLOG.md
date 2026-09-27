# Issue #3691 OrbStack execution record

## H/T/D/C/U

- **H:** The exact PR #3697 auditor snapshot passes its full frozen regression
  suite and canonical raw-only CLI in isolated, network-disabled Docker
  containers.
- **T:** One container ran the exact eight-method unittest file. A separate
  fresh container invoked the CLI against frozen raw/FREEZE/study bytes with
  the external study-manifest SHA pin.
- **D:** 8/8 tests passed. Fresh-container CLI exited 0 with
  `PASS_OFFLINE_STRUCTURAL_AUDIT`, `errors=[]`, and 12/12 source-defined
  corruption controls rejected. Stdout JSON equals the CLI output file.
- **C:** Synthetic offline audit only; no X11, GUI, OS input, model, or XRes
  allocation. This validates PR #3697's exact source snapshot, not arbitrary
  audit completeness or its integration into current main.
- **U:** Finite byte/type/control coverage only; no general security, runtime,
  or product guarantee.

## Preregistration and immutable inputs

- Allocation ID: `issue3691-orbstack-docker-validation-01`.
- Preregistration commit: `ea223bba99683f2e0f96cdf91bb5f338bf49d70c` was pushed
  before either formal container invocation.
- Current main when allocated: `200c0530840128e478dd2a0247b5724bc21104de`.
- Exact candidate: PR #3697 commit
  `f823cbc77e87d2f9ff3456ddf49f2f819bbc340a`.
- Candidate worktree was detached, remained clean, and its remote branch head
  was unchanged after both runs.
- Auditor SHA-256:
  `2852a352117c95dcca56dead2830b868ceeabd70cad72ee852f78d02a9cb852e`.
- Test SHA-256:
  `df18654ec0ce5fe138fc13aee394057cb745d81a4205e9f80911f705c322109e`.
- Study manifest SHA-256 and external expected pin:
  `b74f0662da1f0f84477857de2dbddf87371df7568fac6955dbac98c550cc0ea9`.
- Raw and predecessor FREEZE hashes match `PREREG.json` and PR #3697's
  committed snapshot. The unit suite independently verifies these values.

## Runtime

- OrbStack Docker Engine `29.4.0`, Linux/arm64.
- Exact image:
  `python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db`.
- Image was present before the allocation; no image pull/build or network
  fallback occurred.
- Both invocations used `--network none`, `--read-only`, and a bounded 64 MiB
  `/tmp` tmpfs. Candidate files were mounted read-only; only the evidence
  results mount was writable. Python bytecode writes were disabled.
- Each container used `--rm`; after both exited, `docker ps -a` filtered by
  the pinned image returned no rows.

## Exact invocations

From the evidence branch repository root, with the frozen candidate worktree
at `../issue3691-candidate`:

```sh
docker --context orbstack run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD/../issue3691-candidate/research/issue_3691_audit_integrity_v1:/study:ro" \
  -v "$PWD/research/integration/issue_3691_orbstack_docker_validation_v1/results:/out:rw" \
  -w /study python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db \
  sh -c 'python -m unittest -v test_integrity > /out/unit-tests.stdout.txt 2>&1; test_status=$?; cat /out/unit-tests.stdout.txt; exit $test_status'
```

The second invocation used the same immutable image/source mount and a fresh
container. It invoked `audit.py` once with these arguments:

```text
/study/audit.py
/study/evidence/raw.json
--freeze /study/evidence/predecessor_FREEZE.json
--study-freeze /study/FREEZE.json
--expected-study-sha256 b74f0662da1f0f84477857de2dbddf87371df7568fac6955dbac98c550cc0ea9
--output /out/cli.json
```

The command saved exact CLI stdout in `results/cli.stdout.txt` and the requested
output in `results/cli.json`. An in-container assertion verified byte-equivalent
JSON values, success status, zero errors, and all 12 current-source corruption
controls true. Exit code: 0.

## Receipt discrepancy (preserved)

The candidate source in commit `f823cbc` defines 12 controls, including
`replacement_study_manifest`; this fresh run returned 12, all true. The
committed historical `artifacts/native_audit.json` contains 11 controls and is
left byte-for-byte unchanged. Its SHA-256 is
`36e1e9c64c83be35eef3447d76d78d2f62adff257612184beef4162c5e1fb32a`. This
indicates the historical receipt does not include the final source-defined
control. The new run is the exact current-source Docker result; it does not
rewrite the old output.

Full machine-readable outcome: `RESULT.json`. All hashes for this validation
bundle are in `SHA256SUMS`.
