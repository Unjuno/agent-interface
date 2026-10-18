# Delivery note: Issue #7778 overhead-sensitivity companion

The finite T0 experiment was frozen and executed before PR #7788 appeared.
At freeze and execution, its local branch was
`research/7778-slack-reclamation-t0-20261005`, and its package path was
`research/analysis/slack_reclamation_7778_t0_20261005`. The frozen source commit
and input/code digests remain recorded in `FREEZE.json`; formal outputs and
their receipts remain unchanged.

After the one-shot run, a concurrent PR #7788 appeared using that same branch
name and package path (head `7cc45781f52a54699cb1f4650c5ab2151f0801df`). No
push was made to that branch and its work was not overwritten. This delivery
therefore relocates the already-frozen package to
`research/analysis/slack_reclamation_7778_dispatch_sensitivity_t0_20261005`
on a distinct branch. The relocation does not change the candidate, auditor,
case matrix, raw rows, or audit conclusions.

This is a complementary, separately frozen overhead-sensitivity experiment,
not a replacement for PR #7788: it evaluates dispatch overhead factors 0 and
1 over 18 traces / 108 policy rows, addressing the dispatch-overhead dimension
that PR #7788 explicitly leaves untested. The result remains a finite synthetic
method finding only; it does not justify promoting a runtime scheduling policy.

OrbStack's image content-store read failed before a container could be
inspected or run. The formally executed one-shot candidate and auditor used
local host CPython 3.14.5 on ARM64. This package makes no container, timing,
isolation, host-scheduling, or real-time guarantee claim.
