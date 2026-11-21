# Public owner receipt join — 2026-11-21

## Question and result

Can the recorded public `interface_results` response be joined to an exact
action call, operation ID and target generation, while preserving the verified
input-release and finite late-input-horizon verdict for later effect
attribution?

**PASS_SYNTHETIC_ADAPTER_CONTRACT_ONLY.** At base main
`37868105a6f08d42e5d7bffa0589038cf3665a17`, the candidate adapter parsed the
public MCP result envelope and checked action/cancellation/owner identities,
confirmed release, expiry, horizon sampling coverage and bounded observation
gaps. It derives effect timing from the receipt and an explicit effect-time
input. Unknown time stays unknown; an effect after the verified horizon does
not become eligible task success. A mismatched target generation and an
unverified horizon fail closed.

## Verification

- Adapter + post-authority attribution + comparison measurement + provider
  recorder: **55/55 normal and 55/55 under `python -O`**.
- Current-main supervised Win32 public `interface_results` projection test:
  **1/1 normal and 1/1 under `python -O`**. It retains the owner horizon
  verdict while the action remains UNKNOWN and does not promote task success.
- The initial test run used the default `D:\CodexData\Temp`; six 1 KB
  write-and-fsync operations took 19.0 s, and one adapter case took 90.2 s.
  Repeating in the dedicated worktree-local `.tmp-tests` directory passed in
  under one second. No assertion, timeout, or qualification was changed.
- The retained deterministic A/B/C packet has three raw recorder journals,
  raw request/response/score/image files, measured records, conditions,
  summaries and normal/optimized logs. Its final file manifest is checked by
  `audit_packet.py`.

## Scope and current project status

This is an offline adapter contract experiment. The A/B/C arms are repeated
synthetic records with labels only; there were **zero provider calls, GUI/OS
inputs, Docker actions or WSLc allocation use**. The effect timestamp and
independent score are fixture-supplied. The supervised Win32 contract test
uses a fake owner. Therefore this adds no live task-effect, recovery
reliability, all-attempt provider exhaustiveness or integrated token/latency
comparison evidence.

Repository state cross-check at this turn:

- Current source base is exactly `37868105a6f08d42e5d7bffa0589038cf3665a17`;
  `origin/main` matches it. Issue #57 remains open for matched efficiency,
  standard-caller task success and recovery reliability.
- PR #10340 is an open draft with `dispatch_enabled: false`, no trusted
  allocation attestor and no matched live comparison. This packet touches
  none of its files.
- Issue #58 remains open. The current goal record reports its RC1 doctor HOLD;
  portable packaging/startup passes do not constitute Research Preview
  acceptance.
- The active repository goal also still requires the frozen preview
  acceptance path, standard caller recovery reliability, live matched
  efficiency, and distribution/product acceptance. This packet satisfies
  none of those gates.

No Issue or PR was closed. Keep #57 open. Integrate only after reviewing the
diff against current main and the native public schema; a production result
still requires exact provider-attempt binding and a live, permissioned,
matched run with independently observed effect time.

## Reproduction

From the repository root, run `python
research/integration/standard_mcp_task_ledger_57_v1/native_owner_receipt_join_v1/run_experiment.py`,
then set `TEMP` and `TMP` to a worktree-local writable directory and execute
the tests named in the retained verification logs. Run
`python research/integration/standard_mcp_task_ledger_57_v1/native_owner_receipt_join_v1/audit_packet.py`
to verify the finalized manifest.
