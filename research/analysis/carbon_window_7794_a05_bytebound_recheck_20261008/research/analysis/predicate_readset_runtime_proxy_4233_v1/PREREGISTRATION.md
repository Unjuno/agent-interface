# #4766 — executable Python predicate read tracing

Parent: #4233 (preserve its HOLD and consumed allocation) and analytical #1756 (preserve its finite typed read-set result). This tests a distinct implementation rung: intercept reads made by actual pure Python functions through nested `Mapping` objects.

## H / T / D / C / U

**H.** A nested read-only `Mapping` proxy can record the path reads made during each pure predicate evaluation. A cache keyed by the observed per-path generations will equal full recomputation on the frozen trace, preserve safe hits for irrelevant changes, and reject the false reuse produced by an incomplete static declaration. This is an executable toy mechanism, not arbitrary Python dependency discovery.

**T.** One 8-state trace, two predicates, and four policies yield exactly 64 policy/predicate observations. The predicates are `READY_TO_SUBMIT` (conditionally reads `form.mode`, then `risk.level` only in submit mode) and `TARGET_MATCH` (reads `target.id` and `intent.target_id`). Policies: `FULL_RECOMPUTE`, `DYNAMIC_READSET`, `STATIC_DECLARED` (deliberately omits risk), `STATIC_ALL`. The trace covers toolbar-only changes, submit-to-preview switching, risk changes while observed and unobserved, target changes, and ABA restoration under new generations. `study.py`, `audit.py`, `trace.json`, `test_audit.py`, and this protocol are source-frozen before one formal run. The auditor is stdlib-only and does not import the runner. It recomputes expected values/read paths and applies eight copied-evidence mutations.

**D.** `PASS_DYNAMIC_READSET_SCOPED` requires all 64 rows; exact dynamic/full-recompute parity; zero unsafe dynamic reuse; detection of risk/target generation changes including ABA; at least two valid dynamic hits across unrelated changes; at least one stale reuse by `STATIC_DECLARED`; strictly more false invalidations by `STATIC_ALL` than `DYNAMIC_READSET`; zero auditor errors; and 8/8 mutations rejected. Preserve any complete contrary result as `FAIL_DYNAMIC_READSET_MISMATCH` or `HOLD_NONDISCRIMINATING`; environment/provenance/incomplete-evidence faults are typed STOP/HOLD. No retries, replacements, or tuning.

**C.** The trace author supplies state and per-path generations; writers are assumed to increment them atomically. The proxy records accesses to nested Mapping paths. Direct `dict` base-class calls, globals, attributes, I/O, reflection, mutation, and unwrapped objects are outside this experiment.

**U.** One CPython version, two pure predicates, and eight states. No concurrency, arbitrary-code safety, natural invalidation frequency, timing benefit, model, GUI/task, production ABI, or runtime promotion is established.

## Local environment and exact commands

Cached base: `python:3.12-slim-bookworm`, image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, Linux/amd64, Python 3.12.14. Use `--pull=never --network none --read-only`, no package installation, one CPU, 512 MiB, 64 PIDs, dropped capabilities, `no-new-privileges`, and bounded `/tmp`.

Formal runner command (exactly once; `$SRC` is this read-only source directory and `$FORMAL` is a new writable output directory):

```sh
docker run --rm --pull=never --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus=1 --memory=512m --pids-limit=64 --tmpfs /tmp:rw,noexec,nosuid,size=64m -v "$SRC:/src:ro" -v "$FORMAL:/out:rw" -w /src sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e python -B study.py trace.json /out/raw.jsonl
```

Independent raw-only audit command (a separate container; `$RAW` is the runner's read-only raw JSONL and `$AUDIT` is a new writable directory):

```sh
docker run --rm --pull=never --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus=1 --memory=512m --pids-limit=64 --tmpfs /tmp:rw,noexec,nosuid,size=64m -v "$SRC:/src:ro" -v "$RAW:/input/raw.jsonl:ro" -v "$AUDIT:/audit:rw" -w /src sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e python -B audit.py trace.json /input/raw.jsonl /audit/audit.json
```

## Excluded construction history

- Construction-01: 3 tests ran; denominator test passed, two audit/read-path tests failed because the initial expectation omitted parent Mapping reads. No formal invocation or model/optimizer activity.
- Construction-02: after parent/leaf reads were represented, two tests passed and the audit test still failed because it incorrectly required oracle/static-policy rows to equal the dynamic tracer's exact access paths. No formal invocation.
- Construction-03: all 3 tests passed; runner emitted 64 rows; separate audit returned `PASS_DYNAMIC_READSET_SCOPED`, errors `[]`, and rejected 8/8 copied-evidence mutations. Metrics: dynamic unsafe reuse 0, dynamic false invalidations 0, dynamic unrelated hits 4, static-declaration unsafe reuse 1, static-all false invalidations 9.

The first two construction failures are harness/audit expectation defects and remain excluded from formal evidence. The source and gates were corrected before source freeze. Formal invocations remain 0 at this preregistration.
