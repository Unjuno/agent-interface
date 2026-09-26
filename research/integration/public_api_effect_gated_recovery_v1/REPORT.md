# Issue #4120 result — public API effect-gated recovery v1

Decision: **PASS_EFFECT_GATED_RECOVERY_BOUNDARY_SCOPED**.

## Question

Does bounded recovery through the current public Python API need both an independently scored first application effect and a current application-recipient receipt, rather than trusting native program completion or a post-click pixel observation?

## H / T / D / C / U

- **H:** Native completion is not application success. A `WRONG_FIELD` effect must stop recovery. A `NO_EFFECT` may justify one bounded click-to-focus repair, but the click plus read-only pixel observation does not prove the current Tk keyboard recipient after a later same-pixel focus change. A current recipient receipt should prevent that directed wrong-field retry.
- **T:** Exact current-main public API/X11/core source closure was Git-object verified, then 3 policies × 3 schedules × 2 fresh repetitions = 18 formal cases were executed in two immutable nine-case batches. Each case used a new authenticated TCP-disabled Xvfb and Tk application. All task text/pointer input used `dispatch_golden_v3`; recovery observation used public `observe`. Construction remained separate.
- **D:** PASS requires all 18 rows, both observed batch exits 0, unchanged frozen source, verified empty release for every admitted program, no-authority/no-input public observations, exact effect table, current-B refusal by recipient-gated recovery, raw-only audit errors zero, and all 12 corruption controls rejected.
- **C:** The recipient receipt is cooperative fixture evidence and exact A geometry is supplied. Focus changes are barrier-directed counterexamples. This does not add a generic focus API or task scorer to runtime.
- **U:** No model/provider, token or latency benefit, MCP/CLI parity, cross-toolkit/platform, natural failure rate, automatic rollback, six-task matched efficiency, production default, or `PASS_INTEGRATION_SPINE_SCOPED` claim.

## Frozen source and execution

Preformal public branch head: `c9c6bba4a6fdc02e80761ee596e171da0382c8e9`.
Base main: `210c92b801f9c73e72a31545f5027675c3bb752c`.
Freeze SHA-256: `87bff629a3e80d6bbc977819deff88fd7417045db3212095ad4a205035c47802`.
All 13 vendored repository source files matched exact Git object IDs. Main later advanced to `62f1a25e5c8fc8ad21637fc3e2d7bf391d4a27db` before formal execution; the eight directly used public API/X11/core blobs rechecked byte-identical there.

Formal invocations, each once:

```sh
PYTHONPATH=vendor python run_matrix.py --out formal/batch-0 --rep 0 --display-base 240
PYTHONPATH=vendor python run_matrix.py --out formal/batch-1 --rep 1 --display-base 260
PYTHONPATH=vendor python audit.py formal --freeze FREEZE.json --controls --out AUDIT.json
```

Batch exits: 0, 0. Audit exit: 0. Formal reruns/replacements/exclusions/post-freeze tuning: 0.

## Formal outcomes

Each row below occurred in both fresh repetitions.

| Policy | Schedule | First effect | Recovery input | Final A | Final B | Final effect |
|---|---|---|---:|---|---|---|
| BLIND_RETRY | NO_EFFECT_STABLE | NO_EFFECT | yes | empty | empty | NO_EFFECT |
| BLIND_RETRY | WRONG_FIELD_FIRST | WRONG_FIELD | yes | empty | 77 | WRONG_FIELD |
| BLIND_RETRY | NO_EFFECT_B_AFTER_CLICK | NO_EFFECT | yes | empty | 7 | WRONG_FIELD |
| EFFECT_GATED_CLICK | NO_EFFECT_STABLE | NO_EFFECT | yes | 7 | empty | SUCCESS |
| EFFECT_GATED_CLICK | WRONG_FIELD_FIRST | WRONG_FIELD | no | empty | 7 | WRONG_FIELD |
| EFFECT_GATED_CLICK | NO_EFFECT_B_AFTER_CLICK | NO_EFFECT | yes | empty | 7 | WRONG_FIELD |
| RECIPIENT_GATED_CLICK | NO_EFFECT_STABLE | NO_EFFECT | yes | 7 | empty | SUCCESS |
| RECIPIENT_GATED_CLICK | WRONG_FIELD_FIRST | WRONG_FIELD | no | empty | 7 | WRONG_FIELD |
| RECIPIENT_GATED_CLICK | NO_EFFECT_B_AFTER_CLICK | NO_EFFECT | no | empty | empty | NO_EFFECT |

The key discriminator is `NO_EFFECT_B_AFTER_CLICK`: the effect-gated policy takes a successful public click and a read-only pixel observation, but B becomes the current Tk recipient before recovery admission and receives the retry. The recipient-gated policy reads B and refuses before retry input.

The blind stable control also demonstrates that two native text-program completions can coexist with no task effect. `golden-v3-result-v2.task_success` remained `null`, not `true`, for native completion; application success came only from exact A/B state.

All admitted programs ended with verified empty release. Public observations reported `side_effect_authority=false` and `input_dispatched=false`.

## Independent raw audit

`AUDIT.json` / `AUDIT.stdout.json` report:

- schema `agent-interface/public-api-effect-gated-recovery-audit-v1`;
- rows 18;
- decision `PASS_RAW_AUDIT`;
- errors `[]`;
- 12/12 frozen evidence corruption controls rejected.

Postformal source re-hash matched 21/21 frozen entries. The frozen five-test audit suite also passed after formal execution. The auditor is a separately structured implementation/process by the same author, not external human review.

## Construction record

Construction is excluded from the formal denominator and retained rather than overwritten.

- `construct-01`: target/focus setup did not establish the intended Tk recipients; all first effects were NO_EFFECT.
- `construct-02`: initial B and stable click repair worked, but the directed post-click B transition was not established, so the proposed discriminator was absent.
- `construct-03`: a direct X focus construction again failed to establish Tk internal recipients.
- `construct-04`: switching the public API target to the actual top-level wrapper fixed the target layer, but the post-click B transition still did not hold.
- `construct-05`: fixture focus sequencing (`root` focus then B `focus_force`) established the complete nine-cell expected table.
- `construct-06`: repeated that same excluded table after moving the exact Git-object-verified runtime source into the self-contained vendor directory; this is the terminal pre-freeze construction.

No construction row is pooled with formal evidence.

## Integration meaning

This resolves one bounded result/recovery composition question under #2337/#2789: native completion, app effect, repair observation, current recipient and release are distinct evidence layers. A wrong-field first effect is collateral, not an invitation to retry; a post-click image alone is not a current in-window recipient certificate in this fixture.

The result supports an integration requirement, not a runtime feature promotion. The public route itself remains unchanged. A generic recipient/effect contract and matched six-task end-to-end comparison remain separate work.
