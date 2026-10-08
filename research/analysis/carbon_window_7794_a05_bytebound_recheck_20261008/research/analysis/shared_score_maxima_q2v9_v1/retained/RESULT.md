# Shared-score possible-max contract — retained result

Allocation `shared-score-q2v9-01` completed once from the frozen source. The
disposition is `PASS_SHARED_SCORE_MAXIMA_CONTRACT` for the declared rational
model and finite corpus only.

## H / T / D

**H.** When all candidate scores depend on one justified shared scalar and
candidate-local residuals vary independently within their frozen bounds,
intersecting every winner inequality at the same scalar returns exactly the
jointly possible maximizers, including ties and singleton feasible intervals.

**T.** Exact `fractions.Fraction` arithmetic; 1,470 fixed cases (1,458 grid
cases plus 12 directed discriminators). The three compared sets are the
marginal box, pairwise possible, and shared-witness maxima. No GUI, detector,
model, human, task input, or action authority is involved.

**D.** One frozen invocation returned exit 0, timeout false, and stderr empty.
All 1,470 outputs matched the raw-only crossing-point auditor: 9,326 checks,
zero errors. Ten prospectively fixed copied-record mutations were all
effective and rejected. The shared-witness set is contained in the pairwise
set, which is contained in the marginal box for every case. Across the corpus,
joint membership was narrower than the marginal box in 458 cases and narrower
than the pairwise set in 59 cases. Aggregate candidate-membership totals were
3,932 box, 3,491 pairwise, and 3,432 joint. Every output retained
`action_authority=false` and `task_success=null`.

The output bytes are retained in `records.json.zlib.b64`; `DELIVERY.json`
binds the encoded and decoded SHA-256 values. The process receipt, stderr,
independent audit, and all ten mutation outcomes are adjacent. `verify.py`
reconstructs the compressed bytes without running the candidate and confirms
the saved audit and controls byte-for-byte.

## C / U and environment qualification

This result depends on an authored joint model; it does not validate that real
detections share the declared affine parameter or that their residuals are
independent. The conservative marginal method remains the correct fallback
without that evidence. There is no attention, latency, token, task-success,
detector-calibration, runtime-promotion, or product claim. The candidate and
crossing-point auditor are separate implementations but share Python's
`Fraction` arithmetic and do not constitute independent human review.

The frozen environment requested Linux x86_64 and CPython 3.13.5. Execution
used the locally cached Python 3.13.5 amd64 image in OrbStack on an Apple
Silicon arm64 host; Docker warned about the platform mismatch. The Python
version and `fractions` source hash match the freeze, but the executable hash,
kernel/libc and native CPU environment do not. Exact rational outputs are not
a performance measurement; this is recorded as an environment deviation, not
silently relabeled as the original Linux host.

## Executed sequence

1. `python -S -B -m unittest test_maxima -v` — 12/12 construction tests pass.
2. `python -S -B supervise.py retained` — the sole 1,470-case invocation.
3. `python -S -B audit.py retained` — 9,326 checks, zero errors.
4. `python -S -B controls.py retained` — 10/10 effective mutations rejected.
5. `python -S -B verify.py retained` — compressed evidence and saved audit and
   controls reproduce byte-for-byte; zero new candidate invocations.

The first four commands ran in the pinned local image with network disabled,
read-only container root, and only the temporary experiment directory mounted
writable. The read-only reconstruction was repeated after adding the compressed
publication form; it did not repeat the candidate allocation.
