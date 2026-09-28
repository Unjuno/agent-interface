# H / T / D / C / U — #5215 audit-integrity successor

Successor audit-only validation for Issue #5215 and merged PR #5216. The original probe, plan, and scientific record remain immutable. The retained auditor accepts missing/null/string negative fields, classifies by named booleans without checking timestamps, and conflicts with the frozen plan. This allocation checks the audit boundary against the exact published record; it does not repeat the kernel experiment.

**H.** Required fields and exact types can be enforced, while timestamp and release inequalities can be independently derived; malformed, missing, extra, and contradictory evidence should never be called a pass.

**T.** Input was #5216 `probe-output.json`, blob `d3964da3cbf6524c8193b5a59ed16bdb3611772f`. CPU-only standard-library audit and mutation suite. Cases cover each of four negative fields missing/null/string/integer, unexpected field, identity-negative reversal, non-object records, accepted outcomes inconsistent with fixed time values, release observation before execution end, and plan contradiction. No kernel import/run, runtime change, model, GPU/CUDA, Docker, GUI/input, provider, or network experiment. Initial suite failed 6 assertions due to stale expectations; this failure is preserved in `FAILURES.json`. Revised suite was run against MCP-readback source bytes saved locally.

**D.** Required mutation resistance is evaluated by 8 unit tests. The exact legacy record is classified `HOLD_LEGACY_PLAN_CONFLICT`, not PASS. Cases execution_end_999/1000/1001 have release time 800 earlier than execution end; effect observations 499/699 precede execution start/end. These are evidence validity defects independent of the runtime's historical boolean outcomes.

**C.** Every mutation starts from the same retained JSON object; one key/value changes at a time. Auditor imports neither #5216 probe nor kernel. Expected timestamp facts are a separately fixed table and raw evidence is read-only.

**U.** One host, one retained record, one abstraction report. No statement about actual OS lease enforcement, cross-clock comparability, live effects, or production behavior. Runtime adoption remains stopped pending a reconciled preregistered contract and new valid evidence.

Executed on Windows CPython 3.11.9: `python -m unittest discover -s <local-evidence-dir> -p 'test_*.py' -v`; 8/8 passed. Docker Desktop linux/amd64 is available, but the exact verified local source and evidence were not yet frozen into a container input before the host suite; no container was launched.
