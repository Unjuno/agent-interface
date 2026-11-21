# Calc Fake X composition recheck on current main

## Result

The exact current-main checkout at `bc7e62ed4e48141d6b607e485f411c625d78e62b` passed the focused provider-to-public-MCP-to-Calc task-effect composition test in all four local runs:

| Environment | Normal | Optimized |
| --- | --- | --- |
| Windows CPython 3.11.9 | PASS 1/1 | PASS 1/1 |
| Pinned Docker `agent-interface-xvfb-mcp:late-input-r19` | PASS 1/1 | PASS 1/1 |

The Docker run used the locally available image, network disabled, a read-only source mount, 2 CPUs, 4 GiB memory, 4 GiB swap, and a 256-process limit. No image was pulled. Raw logs and their SHA256 values are listed in `conditions.json` and `SHA256SUMS`. Earlier non-comparable attempts are retained under `prior-stale-checkout-excluded/`.

## Reconciliation

An earlier rerun from an older `897f4896`-based worktree failed on Windows with `trusted_save_controller_unavailable`; an instrumented attempt stopped earlier during owner cleanup. Those observations came from a checkout 66 commits behind current main and are not equivalent to this exact current-main run. The earlier merged-commit note lacked retained Windows raw logs. This packet supplies raw logs from the clean current-main checkout and resolves that comparison for this selector only.

No runtime changes were made. Do not infer that all cross-platform cases are stable from one focused pass.

## Scope limits

This is a Fake X/synthetic provider-planner test. It does not prove live GUI or provider behavior, MAP01 completion, repeated standard-caller task success, recovery reliability, integrated efficiency, or Research Preview graduation. Issue #57 remains open for those gates.

