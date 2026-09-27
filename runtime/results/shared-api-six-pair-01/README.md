# Shared API six-task attempt: retained STOP and recovery limit

Source 7be30aeeeb6592d0666c90f0bb3e9b5045fa39f9; seed 991297. The local freeze
preceded both attempts; this is sequential construction, not a randomized or
model-attested formal performance comparison. Both routes were planned with six
rows. Exact provider configuration, host rendering timestamp and model tokens
were unavailable.

Direct route exited 1 during import before allocation/GUI creation: runtime was
not importable from the direct script invocation. No rerun. The startup receipt
is transcribed from observed terminal failure; no standalone stderr log was
captured. The later source fix adds the repository import root; --help is checked
without PYTHONPATH, but the failed direct task allocation is not replaced.

Persistent route was launched once with explicit PYTHONPATH. It saved tasks 1-3
exactly once, then exited 1 on the second refusal at task 4. Tasks 5-6 were not
attempted. The first task's left-edge anchor was refused MISSING with zero input;
a freshly viewed right-edge point repaired it. Images suggest caret instability,
but this is a hypothesis, not isolated causal evidence. Layout B at task 4 then
caused another no-input refusal. The runner's existing single repair budget had
already been consumed, so it stopped. No gate/budget change or input replay.

The primary viewed each returned image and accepted three SAVED pages. Task-1's
written review incorrectly claimed the token itself was displayed. Its original
consumed review is preserved and a separate correction explicitly retracts that
claim. The page shows only SAVED; exact task values come from independent recorded
submissions/scoring. Therefore this run does not establish accurate token-visible
semantic recognition by the model.

Independent evaluation is false: exact counts [1,1,1,0,0,0], no unexpected or
duplicate submissions. Tracked children exited [0,1,0]; full descendant cleanup
is not claimed. RESULT.json accounts for all 12 planned rows, including the six
direct rows that never started.

#2789 decision: HOLD_INTEGRATION_INCOMPLETE. Shared API component/mixed-app
success does not establish six-task recovery or a matched baseline. Keep current
input gates and stopped evidence unchanged; investigate anchor stability and the
explicit recovery budget before changing continuation policy. No speed/token
comparison is valid here. This evidence identifies an integrated recovery limit;
it is not another successful product acceptance run.

Run python3 verify.py for hashes, row accounting, exact recorded submissions,
both no-input refusals, terminal error and the preserved review correction.
