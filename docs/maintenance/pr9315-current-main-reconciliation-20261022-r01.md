# PR #9315 current-main reconciliation r01

Captured 2026-10-22 JST against current main
`adfc2e37aaee6cabb33db2791f657e621e05081a`. The PR is OPEN/DRAFT at exact
head `76626da8b03df25024d12efb5f1dde2f12c53ed2`, with base recorded by GitHub
as `9bf7ec15ea78eccd752adee1af8d00dc9545eaa0`.

## Disposition

**Do not merge this head. Keep it open pending semantic disposition of the
remaining document/evidence variants.** The supervisor implementation and
evidence have successors on current main through PRs #9320 and #9321; the
design and scoped caller evidence were further reconciled by #9322 and #9323.
This PR has no path whose name is absent from current main, but that fact alone
does not prove that every older byte-level variant has been preserved or
superseded.

At the exact PR head and current main, the merge-base comparison touches 183
paths. 117 have identical Git blob IDs; 66 differ. Those 66 comprise 9
documentation paths, 51 research paths, and 6 runtime paths. After ignoring
end-of-line whitespace, 17 paths retain substantive differences; 49 are
formatting-only in this comparison. The 17 need content-by-content disposition
before the PR can be closed. Refresh the exact head and base before another
state change; these counts describe this capture, not a permanent PR property.

## Safety-significant runtime regression

In `runtime/guarded_x11_v1/cancel_supervisor.py`, this head removes binding and
validation of the cleanup worker's `supervisor_pid`. It treats any PID
different from the retired owner PID as proof of disconnection. Current main
accepts a reused owner resource base only when XRes observes the retained
supervisor process itself at that base; an unrelated client's PID returns
`UNKNOWN` before the release backend is called. The draft also removes the
worker-retirement/exit evidence and related refusal tests. Merging it would
weaken current-main protection against a bystander claiming the old resource
base. Keep current main's stricter path.

## Evidence and follow-up

The PR's exact head, current main, and this finding were recorded in comment
[6325177450](https://github.com/Unjuno/agent-interface/pull/9315#issuecomment-6325177450).
PR #9321 transferred the retained packets and manifest inputs; r01 does not
replace their hash audit. The separately preserved
[PR #9320 standard-caller Xvfb outcome](../../research/integration/public_mcp_prestarted_cancel_supervisor_20261021/pr9320-run-39660663702/README.md)
is now the current scoped held-obligation result. The unique design rationale
in the PR's 12,450-byte `docs/superpowers/specs/2026-10-22-prestarted-cancel-supervisor-design.md`
body is restored on current main beneath a prominent historical/superseded
warning; its appended bytes match the PR blob exactly (SHA-256
`ff8bcff4489afdb25ac09581c56d15c00d2d3e9108cf608343478a4f07919582`). This
preserves the research trail without restoring its unsafe recommendation as
current guidance. Continue by comparing the 17 substantive path contents with
their current-main successors and source manifests. Close #9315 only after
every distinct outcome and useful document delta has a verified current-main
destination and the stale runtime cannot be mistaken for an integration
candidate.
