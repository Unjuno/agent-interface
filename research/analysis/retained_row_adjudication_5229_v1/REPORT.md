# #5229 retained-row adjudication: conditional counts do not fix the contract

Disposition: **PASS_ADJUDICATION_SCOPED** for this retained-byte analytical
check. Original scientific disposition: **HOLD_UNEVALUABLE** under all six
interpretations. This result neither adopts a new runtime contract nor closes
#5229, #5225, or #5215.

The nine saved booleans are internally readable and match the nine calls in the
frozen probe source. They do not establish the missing effect-at-900 control or
resolve the effect-at-700 contradiction. Moreover, changing only the assumed
meaning of release/end changes both the number and identity of conditional
disagreements. Two interpretations produce five disagreements with different
rows. A count of five is therefore insufficient to adjudicate the historical
claim.

## Scope and immutable input

Worker `01a0ff35-2ef3-7911-9911-f31862ad642f`, FINAL-v5. Prospective host-only
claim: [#5229 comment 5964134771](https://github.com/Unjuno/agent-interface/issues/5229#issuecomment-5964134771).
Source intake: `f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549`.
The six exact Git objects under `runtime/results/kernel-time-intake-01/source/`
are pinned by blob ID and SHA-256 in [FREEZE.json](FREEZE.json). The original
probe output is blob `d3964da3cbf6524c8193b5a59ed16bdb3611772f`, SHA-256
`f4c68baed47cbfe8a5ab59980153404b98045829ffa83ea39ace79895c1b3e62`.

The inputs are authored fixture timestamps and stored acceptance booleans,
not measured temporal event logs. The new plan and three authored Python files
were hashed before the first execution. Historical probe, kernel, and audit
code was neither imported nor executed. No model, GUI, GPU, Docker, WSLc,
container allocation, or formal experiment was used. This is ordinary host CPU
analysis of immutable evidence; it does not consume or repeat the old allocation.

## Explicit assumption comparison

The source declares start 500, normal end 700, release observation 800, and
exclusive lease deadline 1000, in nanoseconds on a stipulated common clock.
Execution admission uses `500 <= end < 1000` plus the selected release rule.
The wrong-command row remains expected false. Effect admission uses either
`effect >= 700` (inclusive) or `effect > 700` (exclusive), provided the execution
context satisfies the selected release rule. If that prerequisite is
inconsistent, the effect expectation is unknown rather than a negative
observation. Units, ranges, and scalar meanings are in [PLAN.md](PLAN.md).

| Release interpretation | Effect equality | Conditional disagreements | Unknown rows |
| --- | --- | --- | --- |
| snapshot_only: no release/end ordering | inclusive | 499, 699 effects; 1000, 1001 execution ends (4) | 0 |
| snapshot_only | exclusive | 499, 699, 700 effects; 1000, 1001 ends (5) | 0 |
| post_execution: release >= end | inclusive | 499, 699 effects; 999, 1000, 1001 ends (5) | 0 |
| post_execution | exclusive | 499, 699, 700 effects; 999, 1000, 1001 ends (6) | 0 |
| terminal_includes_release: start <= release <= end | inclusive | 700, 1000, 1001 ends (3) | All 4 effect rows |
| terminal_includes_release | exclusive | 700, 1000, 1001 ends (3) | All 4 effect rows |

All six variants preserve all nine observed values. In the last two variants,
release 800 lies beyond the effect fixture's execution end 700; the four effect
rows consequently have `UNKNOWN_CONTEXT`. These conditional labels are not
replacement runtime observations or promoted scientific results. The complete
54-row table is retained in [adjudication.stdout.json](evidence/adjudication.stdout.json).
The six interpretations are a finite comparison, not an exhaustive account of
every possible receipt semantics.

## Why the original gates remain held

The old plan's baseline includes execution end 700 and effect time 900, but the
probe stores only the execution baseline. Its nine calls/booleans therefore
leave one of the ten individually planned observations absent. The plan also
says effect time 700 is rejected, while the retained legacy audit lists
`effect_at_700: True` among required controls. That conflict is preserved.
Selecting either equality rule does not repair the original freeze. The report
separates `COMPLETE_NINE_OBSERVED_BOOLEANS` from
`INCOMPLETE_EFFECT_AT_900` and `HOLD_UNEVALUABLE`.

No row here fills effect-at-900, certifies release enforcement, establishes
physical effect identity, or validates current kernel/backend behavior.
A future semantic decision needs a separately authorized successor; it cannot
rewrite these original observations, first outcomes, or allocation history.

## Executed validation and publication

The first ordinary validation executions on Python 3.11.9 / Windows completed
at 2026-10-03 01:35:56-57 UTC and are retained without replacement:

- Five unit tests passed, including nine missing-field controls, 45 nonboolean
  controls, and duplicate/extra/nonobject refusal controls.
- The adjudicator checked all six original source identities and generated
  six variants over the nine immutable booleans.
- A separate implementation extracted timestamp roles and call inventory from
  the frozen source AST without running it, independently checked the full
  table, and returned zero errors. All six actual corruption controls were
  rejected: dropped variant, flipped observation, integer substituted for bool,
  invented unknown, promoted gate, and omitted gate reason.

[commands.json](evidence/commands.json) records argv, cwd, UTC boundaries,
exit codes, and stdout/stderr hashes. All raw stdout/stderr byte streams are
retained, including native CRLF and empty streams. Local executable/worktree
paths are published as `$PYTHON`, `$GIT`, and `$REPO`; the original command
receipt remains in the author's private scratch. [PUBLICATION.json](PUBLICATION.json)
pins both versions and declares that sole redaction. This path redaction does
not change any input, output, or verdict. [SHA256SUMS](SHA256SUMS) covers the
published package except itself. No hosted CI result is asserted here.

Only this additive package and one navigation row are proposed. Original
evidence, runtime sources, and other workers' results remain preserved. Main
application still requires the fixed nonauthor committee, current combined-tree
confirmation, repository protections, and expected-old-SHA conditions.
