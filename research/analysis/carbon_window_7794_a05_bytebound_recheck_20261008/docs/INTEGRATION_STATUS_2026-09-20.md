# Integration status — 2026-09-20

This snapshot describes implementation integrated through main
`8b9062f80ddef64d4fde260582a3585b0ed95a59`. It complements the historical
[progress map](PROGRESS_FROM_BASELINE.md); it does not re-audit or supersede frozen
experiments. The goal remains live, useful feedback at human-comparable tempo
with measured correctness, waiting, recovery and model cost.

## What a primary agent can use now

The [public interface](../runtime/USING_CURRENT_INTERFACE.md) supports explicit
Linux/X11 actions and read-only observations. `observe` and `dispatch` can return
the receipt and PNG together using `--review`. `--compact` optionally chooses
reversible event references when their JSON is smaller. The primary model can
choose the next action directly; these entry points require no second model.

The [portable zipapp](../runtime/distribution_v2/README.md) includes this surface
without the research tree. Builds pin one commit for all included source files
and record it in the manifest. The separate
[native MCP adapter](../research/live_control/NATIVE_MCP.md) remains bound to an
explicit research allocation; its managed task lifecycle is not a general-purpose
public desktop session manager.

| Integration | Result for the caller | Source |
|---|---|---|
| Failed native action context | Terminal errors retain the actual failed action rather than only its history | [#3507](https://github.com/Unjuno/agent-interface/pull/3507) |
| Cleanup summary | Routine completion is separated from tracked, owner and descendant verification | [#3510](https://github.com/Unjuno/agent-interface/pull/3510) |
| Host IPC failure receipts | Spawn attempts, task invocation and identity-probe failure are distinguished; probe failures return terminal records | [#3512](https://github.com/Unjuno/agent-interface/pull/3512), [#3517](https://github.com/Unjuno/agent-interface/pull/3517) |
| Public receipt references | File, stdin and immediate action responses share reversible projection; small receipts keep their original form | [#3513](https://github.com/Unjuno/agent-interface/pull/3513), [#3514](https://github.com/Unjuno/agent-interface/pull/3514) |
| Wait evidence | X11 records fixed-delay intervals without asserting a redraw was observed | [#3519](https://github.com/Unjuno/agent-interface/pull/3519) |
| Distribution and CI | Committed source is pinned once; all 28 packaged source paths trigger the portable workflow; CLI tests also run on main pushes | [#3520](https://github.com/Unjuno/agent-interface/pull/3520), [#3522](https://github.com/Unjuno/agent-interface/pull/3522), [#3523](https://github.com/Unjuno/agent-interface/pull/3523) |

## Actual primary use and counterexamples

[Draft #3509](https://github.com/Unjuno/agent-interface/pull/3509) retains direct
host-exposed MCP use: the primary agent entered Calc A1=893/A2=758 and saved XLSX.
Readback confirmed both cells. An explicit observation recovered a partially
painted format dialog. Closing that dialog produced a BadWindow feedback result;
saved-task success and incomplete cleanup verification were retained separately.
The source checkout was inspected after execution, not fully attested at launch.

[Draft #3515](https://github.com/Unjuno/agent-interface/pull/3515) retains use of
the portable runtime built from main `7d12e7afc1b1db163b74a54a821658c8c867e5c7`.
One explicit program entered and saved `portable-3514` in the existing Tk fixture.
The independent effect file was correct and input release verified, but the
action's screenshot still showed the empty, unsaved UI. One additional read-only
observation showed the saved result; input was not replayed. Compact mode kept
the original receipt, so this sample had no compression benefit.

These remain draft evidence pending independent review. They establish narrow
integration observations, not formal adoption or a comparative performance win.
The unsuccessful release-verification run in
[draft #3505](https://github.com/Unjuno/agent-interface/pull/3505) remains unchanged.

## What remains unproved

Before writing this snapshot, the referenced main passed the shared WSL native
integration suite (137 tests), the separate WSL host IPC suite (18 tests), and
the Windows portable distribution suite (5 tests). These are contract/build
checks, not additional GUI allocations or performance measurements.

- **Useful feedback timing:** an action can finish before its screenshot shows
  the effect. `wait_update` is a fixed delay, not redraw confirmation. Backend
  wait clocks and exchange-review clocks do not measure when the model sees a
  useful image or understands task completion.
- **Recovery across lifecycle boundaries:** session-local release/quarantine
  evidence must not be generalized to reconstructed sessions or whole-host
  failures. [#2437](https://github.com/Unjuno/agent-interface/issues/2437) remains
  the relevant open boundary; no automatic restart/replay is justified here.
- **Model cost and quality:** JSON byte selection is not token accounting.
  Same-model/task/environment comparisons still need actual input-token/cost
  records, task correctness and recovery accounting. No human-tempo claim follows
  from the successful single runs.
- **Research transfer:** the GTK resident-policy evidence in
  [#3511](https://github.com/Unjuno/agent-interface/pull/3511) has a causal-policy
  follow-up in [#3518](https://github.com/Unjuno/agent-interface/issues/3518).
  Its app-specific title checks and settle delays are not a generic redraw gate.
  Sensor construction remains with the separate research work; this integration
  stream consumes validated results rather than developing sensors itself.
- **Coverage and product completion:** the new primary-use results cover Calc
  and a small Tk fixture. They do not establish the broader desktop, DOOM,
  Mindustry, OpenTTD and Luanti coverage, nor a finished Agent Market product.

Next integration decisions should reduce unnecessary interaction or improve
usable feedback while preserving these distinctions. Frozen failures remain
evidence; passing contract checks alone is not a reason to promote an unproved
control policy or claim a performance improvement.
