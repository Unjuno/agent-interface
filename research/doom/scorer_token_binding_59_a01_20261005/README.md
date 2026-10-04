# Scorer intent-token binding A01 — Issue #59

## H / T / D / C / U

**H.** For the current V15 scorer event shape, `id` alone is insufficient to
join an accepted intent to an input admission. If their `intent_token` values
conflict or either identity is missing, the scorer join must fail closed before
it can report admission-bracketed progress.

**T.** Pin the exact open #7664 parent candidate and JSONL consumer. Run one
frozen three-case candidate invocation: (1) the pinned baseline with one shared
`id` but mismatched acceptance/admission tokens; (2) the successor with matching
tokens and a post-admission positive scorer sample; and (3) successor controls
for mismatched and missing admission tokens. An independently implemented
raw-only auditor checks source/input hashes and all four dispositions. The
container attempt is recorded separately; this finite standard-library test is
not represented as a container run.

**D.** `PASS_TOKEN_BINDING_SCOPED` requires the baseline to reproduce a false
positive, the successor to preserve the matched-token positive, reject both
mismatched and missing tokens, and the raw-only audit to pass. Otherwise retain
`FAIL_*`/`HOLD_*` without changing the cases.

**C.** A globally unique program ID could already prevent this mismatch in
valid runtime history. That does not make contradictory same-ID event rows safe
to accept, and this test does not establish that such a conflict occurred in a
live episode.

**U.** The cases are deterministic, runtime-shaped JSONL records. They do not
establish a live source conflict, useful game effect, causation, recovery,
threat response, physical release, or MAP01 outcome. Execution used host Python
3.14.5 on macOS because OrbStack image inspection failed on a missing
containerd content blob; no Docker container or game/input process ran.

## Reproduction

From repository root, after the parent #7664 package is present:

```sh
python3 research/doom/scorer_token_binding_59_a01_20261005/run_a01.py
python3 research/doom/scorer_token_binding_59_a01_20261005/audit_a01.py
```

The source freeze and first raw output are retained under `results/a01/`.

Pre-candidate wrapper correction: the first invocation stopped at source preflight because the runner compared six hashes while the freeze pinned nine. Candidate invocation count remained zero and no raw result was produced. The wrapper now compares every frozen source entry; the corrected wrapper and freeze are committed before the single candidate invocation.
