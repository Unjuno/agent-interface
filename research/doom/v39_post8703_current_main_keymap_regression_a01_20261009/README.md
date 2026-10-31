# Current-main keymap failure regression after PR #8703

Main commit `cef53dbe8d131a8e116c92b5c79257f1db5f77b3` adds one test to `research/live_control/test_input_owner_v12_explicit_up_cancel.py`. The exact current-main test-module bytes were loaded with `git show` and executed dynamically against the unchanged production source modules from main `74fc81e0a447ad05e4a2220b16d7949979635fb9`. The production source did not change in #8703; that commit is test-only. All seven tests in the resulting current-main module passed normally and with `-O`.

Together with the 100/100 normal and optimized V39/V15/ExecutorV13 regression recorded in sibling package `v39_post8699_current_main_regression_a01_20261009`, this closes the test delta through #8703. Scope is synthetic fake-X/source regression only; no real X server, physical input, GUI, game, or live allocation was used. It does not establish physical key state or game consumption.
