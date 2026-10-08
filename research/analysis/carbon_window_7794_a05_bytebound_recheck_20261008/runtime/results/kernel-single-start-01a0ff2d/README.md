# Kernel single-start repair — Issue #6852

This is ordinary local engineering verification of the promoted sequential
`RequestLifecycle` API, not a formal scientific allocation. Original research
allocations, frozen sources and historical outcomes are unchanged.

Issue: <https://github.com/Unjuno/agent-interface/issues/6852>.
Worker: `01a0ff2d-be6f-78d3-ad7c-497514c9079f`, policy `FINAL-v5`.
Baseline main: `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`.
Environment: native Windows, CPython 3.12.10, standard library, one process.
No backend, model, GUI, input, GPU, container or formal retry was used.

## Defect and minimal repair

After `begin_execution(A)`, the lifecycle remains AUTHORIZED while A's execution
receipt is pending. A second `begin_execution(B)` was accepted and replaced
`self.request`, causing A's later receipt to fail command matching. The same
request could also be begun again. The repair rejects every later begin after a
request has been accepted and preserves A for receipt/effect matching. A rejected
first begin remains non-consuming; cancellation still requires verified release.

The state/API shapes are unchanged. This guard does not synchronize concurrent
threads, prevent direct writes to public attributes, guarantee exactly-once OS
execution or establish live computer-control benefit. Callers must serialize
lifecycle transitions and use a fresh lifecycle for a subsequent command.

## Verification and decision

- H: one lifecycle accepts at most one successful begin and retains its identity.
- T: existing 18 kernel tests, three added regression methods, and a separate
  stage/command transition-table oracle over nine events and all lengths 1–4.
- D: the baseline must expose duplicate-begin rejection failures; the repair must
  pass the kernel suite and match the oracle on every enumerated transition.
- C: this tests sequential API admission; backend concurrency and input dispatch
  are separate and were not observed.
- U: finite enumeration is bounded to 7,380 traces and 28,602 transitions,
  fixed valid identities/times, two command IDs, one action, positive effect,
  malformed binding, and released/unreleased stop controls. It is not an
  exhaustive proof over arbitrary inputs or thread interleavings.

| Check | Baseline | Repaired source |
|---|---|---|
| Kernel suite including regressions | exit 1, three assertion failures | exit 0, 21/21 methods |
| Reference comparison | 1,168/7,380 traces mismatch, exit 1 | 0/7,380 mismatch, exit 0 |
| Core contract regression suite | not repeated on baseline | exit 0, 65/65 |

The cancellation and malformed-first-begin controls remain accepted/refused as
specified. The baseline replay is a regression check against its Git blob; it
does not rerun any retained experiment. The oracle uses an independent transition
table, but was authored by this same worker; it is not non-author review.

All fixture time fields are nonnegative integer nanoseconds (`ns`) in a stipulated
single monotonic time domain. The observation is captured at 100 ns, authorization
at 200 ns, begins at 300–303 ns, execution receipt spans 500–700 ns, release is
observed at 800 ns, effect at 900 ns, and the lease ends at 1,000 ns. These values
are authored fixtures, not measured latency. No timing/performance inference is
made from unittest's elapsed time.

## Reproduce from repository root

```sh
python -m unittest -v runtime.kernel.test_kernel
python -m compileall -q runtime/kernel
python runtime/results/kernel-single-start-01a0ff2d/check.py --output /tmp/fresh-fixed-model.json
python runtime/results/kernel-single-start-01a0ff2d/check.py --source-ref 11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d --output /tmp/fresh-baseline-model.json
```

Choose new output paths appropriate to the host. The checker exclusively creates
its output and leaves recorded results unchanged. Baseline comparison is expected
to exit 1. The emitted digest covers every compared event row in deterministic
enumeration order; the source and script reproduce the full comparison. Result
JSONs retain all mismatch denominators and the first eight witnesses.

`before.txt` removes only the private local checkout prefix from traceback paths.
The original pre-redaction bytes are retained outside the public checkout. Other
logs contain native Python output; `*.exit-code.txt` records each runner's actual
exit independently of PowerShell's output pipeline. `MANIFEST.json` hashes the
public retained files, checker, repaired source, regression tests and unchanged
contracts dependency; it excludes itself and records original Git source hashes.

Hosted CI, non-author approval, current-main combination review and main
application are separate states. This local result does not certify those gates.
