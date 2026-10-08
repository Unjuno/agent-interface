# Main integration readiness, 2026-10-02 JST

PR #6077 merged to main as 4526e4b19b6addebca5b498a8047f25929d39846.
Its exact head was 0c20566f59a2bc65b8a945c162d57febef053189. Two hosted
checks were still queued: a duplicate Native MCP push run (the PR run had
succeeded on the same head) and the retained-static-evidence workflow.
Under the user's explicit local-CI fallback instruction, both commands of the
latter ran on a source-frozen WSL archive with Python 3.13.5: 16 current
static tests passed, and immutable historical records/controls reconstructed
exactly with zero new engineering trials. Full command results and original
stdout/stderr are in parent-static/. This is not hosted-job completion.
Other applicable hosted X11/native/build/CLI/review/contract/audit checks passed.
The first GitHub merge request failed with a GraphQL service error; OPEN status
and clean compatibility were checked before the successful ordinary retry.

Preparation failure: local gate directory -01 was allocated, then git archive
rejected nonexistent runtime/__init__.py (exit 128), before either test ran.
It remains in results-local/. This paragraph records that original tool failure;
it is not an original process stdout file. The corrected preparation used -02.

The child was rebased onto this exact main, producing
f26dfb37af9571dabf6010afcebb17bdc01dde1e. All 235 changed paths and their Git
blobs matched the former child head 2ade22fa1d753cf509ac27c8567d935d8fbe82c2.
The exact Native MCP workflow Node selection passed 156 tests; the shared
local CI passed 374 protocol and 176 harness tests. Original logs and source
attribution are in child-main/. These are contract results, not another live
study or performance measurement. Frozen live-study files were unchanged.

The dependent evidence branch was rebased too; all 189 additive blobs remained
identical to de2a5212882ffa646df975ac52749c1901b2f4b9. Both branch updates used
one atomic push with exact previous-head leases. No other agent's update was
overwritten. PR #6114 remains the evidence publication.

While these local checks ran, PR #6101 was closed without merge at
2026-10-01T15:17:50Z. Closure had no explanatory comment. Retargeting returned
"Cannot change the base branch of a closed pull request". Reopening and main
adoption are held pending clarification of the closing intent; successful local
tests do not override this external action. No stopped-inspection main adoption
is claimed. Current code remains available in its rebased branch.

This report records readiness and actual integration state. It does not establish
general efficiency, human reaction speed, token savings, GUI uncertainty
calibration or full Docker/WSLc parity. Original failed outcomes remain retained.
