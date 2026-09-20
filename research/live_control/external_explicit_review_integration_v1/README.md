# Integration review of external explicit-window evidence

Source: merged PR #3468, commit 9a1a92d62c415c90a12540a6fa04797a0abb3840,
research/results/native-handle-explicit-review-01. No production change adopted.
The published auditor was inspected, then rerun against exact Git blob bytes
in a fresh local staging directory. Its 16 checks and result matched the
published audit object exactly. The separate p2-effect.json was additionally
parsed and compared with the effect embedded in the positive-control raw row;
they matched. Verification and recomputed audit are retained here.

Reproduction layout matters: the archived auditor reads an `out/` sibling,
while the published raw files sit beside it. Stage audit.py at a temporary root
and raw.jsonl, xtest-emissions.jsonl and p2-effect.json under its out/ directory;
run the unmodified auditor there. Compare generated out/audit.json with the
published audit.json. Never run in or overwrite the frozen evidence directory.

Integration decision: retain the existing explicit review/rebinding boundary
for guarded-handle workflows. This scoped result supports predecessor-alias
revocation following explicit review on the pinned experimental bridge. It does
not justify implicit retargeting, treating matching pixels as new authority,
promoting that bridge into the direct public API, or closing the real-time
research objectives. The replacement used a different XID; #3464 XID reuse
remains unresolved. #3465 stopped before a decision due to control-channel EOF;
it supplies no edge-action or cleanup success evidence.

This is local reproduction of an external published audit, not a newly
independent auditor or new container allocation. No sensor work, GUI input,
formal allocation retry, roadmap closure, or performance claim.
