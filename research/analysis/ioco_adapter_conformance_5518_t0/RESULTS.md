# Issue #5518 T0 execution record

**Disposition:** `PASS_T0_IOCO_SYNTHETIC_CONTRACT`  
**Allocation:** `issue-5518-ioco-synthetic-t0-20260930-01`  
**Base main:** `bf95329e9c787fa600f92e1f3b207cc77083fee4`  
**Frozen source commit:** `798efe7ba45e22f393043878c5c600a1980afa4a`  
**Freeze SHA-256:** `2ae24ccc0b9728c22e3808a64ec4c02454a91980368b80ee8eb87cf0b0ee525f`

## H / T / D / C / U

- **H:** Input-conditioned output inclusion accepts visible-equivalent traces despite declared internal batching/retry differences; rejects target, freshness, authority, and false-success outputs at the first forbidden prefix; and distinguishes explicit UNKNOWN/QUIESCENT from missing output.
- **T:** One frozen run of eight authored finite traces in Docker Desktop 4.48.0 / Engine 28.5.1, Linux/amd64, image `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`. Network disabled; source bind mounted read-only; candidate output on a separate writable mount. The independent auditor ran once in a second container. Candidate invocation count: **1**.
- **D:** The frozen gate passed: three conforming traces (including the hidden-batch trace and delayed UNKNOWN/explicit QUIESCENT), four forbidden-output traces rejected, one missing-output trace returned UNKNOWN; visible input/output projections matched while instrumented raw traces differed; all four auditor mutation controls were rejected.
- **C:** Deterministic hand-authored finite profile, exactly one visible output per input, with internal implementation events explicitly ignored. This is not a full ioco algorithm or an empirical timing study.
- **U:** No real adapter, GUI, model, physical input, runtime effect, production ABI, cross-platform behavior, or latency distribution was tested. The finding is relative only to this authored contract and corpus; it does not establish runtime or product safety.

## Commands and outcome

Construction suite, run in the pinned image before the frozen candidate:

```sh
python -B -m unittest discover -s tests -t . -p 'test_*.py' -v
```

Result: **12/12 passed** after checksum verification. The frozen candidate then ran once with `python -B run.py --output /out/raw.json --root /src`; exit code 0. A separate container ran `python -B audit.py --raw /out/raw.json --output /out/audit.json --root /src`; exit code 0. No retry or second candidate invocation occurred.

Audit: zero errors; statuses `CONFORMANT=3`, `NONCONFORMANT=4`, `UNKNOWN=1`; all four mutation controls rejected. Raw result SHA-256: `f5036159dbe4d49a8da87b1baf74cb3028f86583a320d8166a7c9e39bee48e4b`. Independent audit SHA-256: `f497501dce122b613e10d842b31986205975ca451eb8b7ab39a5b2a74d875cb1`.

STOP/failure record: the frozen run itself had no failure or STOP. The first GitHub audit-only CI attempt stopped before audit recomputation because its workflow expected `image_pull_step`/`candidate_step`/`audit_step` fields that the committed execution sidecar does not define (`KeyError: image_pull_step`). The check referenced the wrong schema; this did not affect the already completed local candidate or independent audit. The workflow was corrected to check the actual allocation count, exit codes, disposition, and no-retry fields. The failed run is preserved; the candidate was not rerun.
