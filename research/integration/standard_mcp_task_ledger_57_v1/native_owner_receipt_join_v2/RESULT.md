# Native owner receipt join — stricter R02 — 2026-11-21

## Question and result

Can the caller journal prove that the public `interface_results` owner receipt
belongs to the same recorded `interface_dispatch` event, action call ID,
operation ID and target generation before effect attribution uses its expiry,
release and finite neutral-horizon bounds?

**PASS_SYNTHETIC_ADAPTER_CONTRACT_ONLY.** The candidate adapter now requires
both a unique recorded `interface_dispatch` and a unique recorded
`interface_results` call. It joins the lookup's action call ID to the
dispatch event, and compares the dispatch operation ID and target generation
with the later public action/cancellation/owner receipt. It then requires a
confirmed recovery and a verified, sufficiently sampled finite horizon. A
dispatch operation mismatch, cancellation generation mismatch or unverified
horizon fails closed. An unknown effect timestamp remains unknown; a time
after the verified horizon cannot qualify as authorized task success.

The preceding `native_owner_receipt_join_v1` packet is retained unchanged. Its
review exposed the missing dispatch-event join; v2 adds that negative
regression rather than rewriting the earlier packet or its manifest.

## Verification

- R149/R281 effect attribution + comparison measurement + recorder + adapter:
  **56/56 normal and 56/56 under `python -O`**.
- Current-main supervised Win32 public `interface_results` projection test:
  **1/1 normal and 1/1 under `python -O`**. The action remains UNKNOWN and
  task success is not promoted by owner release/horizon evidence.
- The first run in the default TEMP volume was slow: six 1 KB write-and-fsync
  operations took 19.0 s. Using a dedicated temporary directory on the
  worktree's C volume, the 56-test runs completed in 1.18 s and 1.20 s. Test
  assertions and timeouts were unchanged.
- The A/B/C recorder packet preserves synthetic dispatch and owner lookup
  responses, provider attempt, observation, independent fixture score, raw
  request/response/state/image bytes, measured records, conditions, summary
  and logs. The final manifest covers **40 files**; the packet audit reports
  40/40 verified and zero mismatches.
- `git diff --check` passes.

## Project-state cross-check and limits

At freeze, `HEAD` and `origin/main` both equal
`37868105a6f08d42e5d7bffa0589038cf3665a17`. Issue #57 remains open. PR #10340
is a non-dispatching draft and its file list does not overlap this packet or
adapter changes. The repository's current-goal/roadmap/organization records
continue to identify live matched efficiency, standard-caller recovered task
success/reliability, Research Preview acceptance and distribution/product
acceptance as open gates.

All experiment arms are synthetic journal records: the three A/B/C labels do
not represent different systems. There were zero provider calls, GUI or OS
inputs, Docker actions or WSLc allocation use. Effect time, task score and
comparison pins are fixture-supplied, and the supervised owner test uses a
fake owner. This demonstrates identity-join behavior only. It does not prove
live owner truth, provider-side retry exhaustiveness, independent scorer
identity, live task success, recovery reliability, matched efficiency or
Research Preview graduation. No Issue or PR was closed.

## Reproduction

Run the packet's `run_experiment.py` from the repository root. For tests, point `TEMP` and `TMP` at a writable
worktree-local directory, then run the modules listed in
`verification-normal.log` and `verification-optimized.log` from
`research/integration/standard_mcp_task_ledger_57_v1/`. Verify the packet with
`python research/integration/standard_mcp_task_ledger_57_v1/native_owner_receipt_join_v2/audit_packet.py`.
