# Issue #57 App Server to durable Calc ledger composition — R01

## Frozen scope

- Source base: current main `490d7bcb4d84927116112e5ff348cdeadfc489d6`.
- Evidence branch before this packet: `research/win32-expired-authority-delayed-effect-r24-20261123`, HEAD `9933a5a2572eb49bde46c6f1c7cde88df9c272c9`.
- Changed test under evaluation: `research/live_control/test_grounding_appserver_usage_transport.py`.
- Host: Windows, CPython 3.13.14, Pillow 12.2.0.
- Allocation: one process-local temporary synthetic fixture per test; no external allocation, model provider, GUI, native input, Docker, or WSLc.

## Hypothesis and decision rule

The existing App Server grounding transport, v3 caller, and Calc durable-allocation writer are individually tested, but their failure/usage boundary may lose provider identity or token usage when composed. PASS only if the JSONL test peer's exact thread/turn identity and per-turn usage survive the grounding adapter, become one failed v3 model attempt, are fsynced into a durable Calc allocation, and pass `audit_allocation()` without promoting execution/effect success. Run the same fixed fixture normally and under `-O`; both runs must pass without retry.

## Fixture

The fake JSONL peer reports one completed turn with turn ID `turn-ledger-1`, thread ID `thread-ledger-1`, input 1,234, cached input 234, cache-write input 0, output 56, and reasoning output 12. Its answer body is `{}`, intentionally invalid for the compiled grounding schema. The caller must preserve the observed usage and identities while returning `CALLER_FAILED`; no execution or effect receipt may be written.

Commands:

```text
py -3.13 -m unittest research.live_control.test_grounding_appserver_usage_transport -v
py -3.13 -O -m unittest research.live_control.test_grounding_appserver_usage_transport -v
```

Raw stdout, stderr and exit codes are stored beside this file. The test has no retry and uses isolated temporary directories.

## Scope limit

This tests synthetic transport and local durable accounting only. It does not call a live provider, prove provider-side usage completeness, connect `ProspectiveRun`'s three-arm lifecycle to a live adapter, or establish GUI task success, efficiency, reliability, or Research Preview acceptance.
