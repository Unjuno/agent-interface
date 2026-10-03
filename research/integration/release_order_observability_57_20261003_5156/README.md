# Release-order observability at the aggregate kernel receipt

A finite construction retains two alternative histories with the same complete
`ExecutionReceipt` projection and opposite final one-key states. Under the declared
snapshot semantics, the aggregate receipt alone cannot decide whether release followed
the last input. A simple `release.observed_ns >= execution.ended_ns` comparator also
refuses valid cleanup-before-bookkeeping histories in this domain. This is a scoped
information-sufficiency result, without a runtime repair or a physical-backend claim.

Parent [#57](https://github.com/Unjuno/agent-interface/issues/57), following the explicit
residual of merged [#6861](https://github.com/Unjuno/agent-interface/pull/6861) and closed
[#6855](https://github.com/Unjuno/agent-interface/pull/6855). The
[prospective scope claim](https://github.com/Unjuno/agent-interface/issues/57#issuecomment-5964860110)
and existing
[worker record](https://github.com/Unjuno/agent-interface/issues/5156#issuecomment-5963705617)
precede execution. The method is the repository's
[finite analytical route](../../../docs/RESEARCH_METHOD.md).

- [Report and argument](REPORT.md): observed counts, an exact projection collision,
  comparisons, scope, and empirical residual.
- [Prospective H/T/D/C/U and variable definitions](PLAN.md), [case set](cases.json),
  and [18-input freeze](FREEZE.json).
- [Selected source identity](SOURCE.json), exact [kernel copy](frozen_kernel/), and
  unchanged [earlier construction source archive](construction_sources/SOURCE.json).
- [Original primary rows](run01/raw.json), [separate raw-only audit](run01/audit.json),
  [attempt marker](run01/ATTEMPT.json), and [invocation receipts](run01/RUN_RECEIPT.json).
- [Post-run readback](run01/readback.json), [readback-only source](readback_checks.py),
  [original setup qualifications](SETUP_NOTES.md), and [later inspection notes](POSTRUN_NOTES.md).
- [Manifest](SHA256SUMS.txt): all other public package files, including fixed first
  outcomes. The manifest excludes itself to avoid self-reference.

Primary candidate and auditor ran once each at `run01`, with zero retries. Both exited
0 without reaching their diagnostic timeout. Integrity is `PASS`; the model decision
is `FAIL_TERMINAL_RELEASE_IDENTIFIABILITY`. These are different predicates. The first
says the retained evidence matches its frozen construction and controls; the second
rejects terminal-state identifiability from this projection under the model assumptions.

For a new independent reproduction, export the exact package and its Git history into
a private scratch directory and choose a **new execution identity/output**, retaining
the originals. Do not run `run_once.py` over this consumed `run01`. The runner and
programs refuse existing original capture/data paths. Ordinary construction source can
be checked with `python -B -m unittest -v construction_checks`; its original pre-freeze
execution used the byte-identical former name `test_construction`, as disclosed in
[SETUP_NOTES.md](SETUP_NOTES.md). The readback checker imports no producer, auditor or
kernel and does not execute their programs.

Native Windows CPython 3.12.10, stdlib only; no operating backend, actual input, model,
container, live/formal allocation, GPU, application effect, latency, or token accounting
was used. Source/data/history are retained rather than promoted into runtime semantics.
