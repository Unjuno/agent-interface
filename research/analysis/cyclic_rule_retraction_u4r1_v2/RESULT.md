# Issue #4449 — formal outcome: `STOP_AUDIT`

## Decision

The one frozen 256-condition OrbStack invocation completed with process exit 0
and emitted all 256 rows. The frozen audit reconstructed the independent
least-model oracle with `errors=[]`; the affected-cone candidate and full
rebuild matched that oracle on every row. Descriptive raw counts are 0
candidate/full mismatches, 0 deletions adding grounded claims, 36
local-support false-retained claims, and 200 blind-invalidation
false-removed claims.

The predeclared evidence gate did **not** pass. The frozen auditor reports
`STOP_AUDIT` because (1) the frozen condition-corpus digest is
`0af2eedbb7586a0d45b8a0b651833813f406c0dea57523b08e16cd450e17aa57`, while
the actual retained newline-delimited condition bytes hash to
`80469fe9fd4434682ff00eb101417b053cd5b683edde7573043d3de1b24461a9`; and
(2) only 2/10 copied-evidence corruption controls were effective. The digest
discrepancy was traced to the pre-freeze hash calculation encoding the two
characters `\\n` instead of newline bytes. The corruption controls mutated
fields in the first row, a NO_CHANGE case whose fields are already empty.

These are frozen-gate failures. Therefore this allocation has **no formal
scientific PASS or FAIL disposition**, notwithstanding the semantic
observations above. The formal run, frozen audit output, and raw files are
immutable; no rerun, replacement, row exclusion, threshold change, or repair
was made. Any renewed audit requires a separately frozen successor against
these exact immutable bytes.

## H / T / D / C / U

- **H:** clearing and rederiving the deleted rule's surviving dependency cone
  should equal full least-grounded recomputation; deletion should not add
  claims. Local-support pruning may retain an unsupported cycle; blind
  invalidation may discard alternate support.
- **T:** all 64 rule masks over roots E0,E1, claims A,B, and six fixed positive
  rules; one no-change row and every active single-rule deletion (256 total).
  OrbStack, pinned Linux/arm64 Python image, CPython 3.12.14, standard library,
  network none, read-only source/root, bounded CPU/memory/PIDs.
- **D:** requires source/input/process integrity, exact 256-row reconstruction,
  candidate and full-rebuild oracle equality, both named counterexamples, zero
  audit errors, and 10/10 effective corruption controls. The run completed, but
  the frozen input-hash and corruption-control gates failed, so disposition is
  STOP rather than PASS/FAIL.
- **C:** fixed complete positive rule set, roots unchanged, one existing rule
  removed per case. Construction demonstrated an external-support cycle and
  an alternative-support case.
- **U:** two-claim finite model only; no arbitrary-graph runtime, concurrency,
  authority, performance, GUI/task, model-utility, or production claim.

## Execution record

Formal raw rows SHA-256:
`c7b2f3dacf65a5d5c1799883ce037d8ffab039de10472e9efb2c4f238b0c5a0e`.
Formal condition bytes SHA-256:
`80469fe9fd4434682ff00eb101417b053cd5b683edde7573043d3de1b24461a9`.
Frozen study source SHA-256:
`c28df3d35bba2a385fb5bc7d115e44a69c45ff338a198bdfe02fbdd1a383acd9`.
Frozen auditor source SHA-256:
`f9146d0d1ca1b79601b08408186aa92dafcd119ce933f2de87c49c383308f2cd`.

The exact formal runner summary was:

```json
{"exit_code": 0, "phase": "formal", "rows": 256, "rows_sha256": "c7b2f3dacf65a5d5c1799883ce037d8ffab039de10472e9efb2c4f238b0c5a0e"}
```

The formal invocation used the following container command (source mounted
read-only; only `results/` writable):

```sh
docker --context orbstack run --rm --pull=never --platform linux/arm64 \
  --network none --read-only --cpus=1 --memory=256m --memory-swap=256m \
  --pids-limit=32 --cap-drop=ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --workdir /study \
  --mount type=bind,source="$STUDY",target=/study,readonly \
  --mount type=bind,source="$RESULTS",target=/evidence \
  --entrypoint python \
  sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e \
  /study/study.py --phase formal --out /evidence/formal01
```

The separate auditor used the same isolation flags and mounts, with command
`python /study/audit.py --phase formal --run /evidence/formal01 --report /evidence/formal01/audit.json`.

Full process receipt, condition/input files, all rows, and the unmodified first
audit report are retained under `results/formal01/`. Construction raw and its
initial 9/10-control STOP plus corrected 10/10 construction audit are retained
under `results/` and documented in [CONSTRUCTION.md](CONSTRUCTION.md).
