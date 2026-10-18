# Execution record

- Base/current-main commit: `28b6f0fc0dd3cf6d798d97ee608a409ce773e409`.
- Work branch: `fix/59-hud-value-domain-currentmain-20261008`.
- TDD red command: `python -m unittest test_source_refresh_v1 test_doom_action_validity_contract_v1 test_doom_action_snapshot_v1 test_doom_typed_observation_epoch_exact -v`.
- TDD red outcome: exit 1, 36 test methods, 19 failing subcases. Failing boundaries were health 0/201 and ammo -1/1000 where not already rejected, with 0/201/-1/1000/bool/float accepted by snapshot construction.
- Post-fix command: `python -m unittest test_doom_signal_value_domain_v1 test_source_refresh_v1 test_doom_action_validity_contract_v1 test_doom_action_snapshot_v1 test_doom_typed_observation_epoch_exact -v`.
- Post-fix outcome: exit 0, 39 tests in Windows Python 3.12 and Ubuntu WSL Python 3.12.
- Static check: WSL Python `py_compile` over the five changed source modules and five associated test modules; exit 0.
- Whitespace check: `git diff --check`; exit 0.
- WSLc runtime/container invocations for this work: 0. No WSLc image/container operation, Docker operation, live GUI, model, or game was used.
- No retry of any previous formal allocation occurred.
