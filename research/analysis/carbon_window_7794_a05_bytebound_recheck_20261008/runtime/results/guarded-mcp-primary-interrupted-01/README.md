# Interrupted public guarded MCP primary trial

Status: **INTERRUPTED_NOT_SUCCESS**. Code under trial: `bca81d1d0`.
The user-authorized WSL shutdown terminated this allocation. After reboot no
fixture/relay/Xvfb process remained. Transport exit is 1. There is no final
independent evaluation, submission history copy, finish marker, or verified
fixture cleanup. Do not infer six-task success from completed input receipts.

The archive preserves the original allocation, setup, 21 retained relay requests
and replies, server journal/images, host timing and review notes, plus the fixture
source and earlier contract-check logs. Original files are unchanged.
`summary.json` indexes authoritative reply IDs and reports missing evidence.

A second defect was discovered during reconciliation: every original
`primary-review.jsonl` entry cites the initial source/call ID. Its mutable latest
reference did not follow responses. These notes are invalid as source-bound
review evidence. They are not retroactively rewritten. The raw replies retain
separate real sources, including a navigation failure and a stale-alias refusal.
There is no claim of matched speed, model token savings, or human-like tempo.

The host adapter now offers `recordRelayReview` with an explicit retained reply
path and an exclusive new receipt path. It derives source/call/image hashes from
that file and refuses ambiguous or missing image evidence. This establishes
attribution only: a caller's declaration is not proof of visual understanding.
New experiments must use fresh allocations and explicit review receipts; never
resume an old session alias after a WSL restart or silently replay its input.

Run `python3 verify.py` in this directory to check archive integrity without
extracting files. Integrity is not an experiment-success verdict.