# Construction record

Before formal allocation, `python3 -I -B -m unittest discover -s research/analysis/route_blind_adjudication_7436_t0_a01 -p 'test_package.py' -v` passed 5/5. The suite covers deterministic seeded packets, explicit-canary removal, actual synthetic source filenames/pathnames, rubric/evidence retention, score schema/coverage/pointer checks, commitment-before-reveal and postcommit tamper refusal.

The first construction run failed 1/5: the score-tamper test wrote `not_useful` onto a record that already had that value, so it did not mutate the commitment. This construction failure is preserved in chat/command output; the test was corrected to choose a guaranteed different score and the suite then passed 5/5. No formal candidate or auditor invocation occurred before the correction.

`python3 -I -B -m py_compile` passed for presenter, candidate, auditor and tests. `git -c core.whitespace=cr-at-eol diff --check` passed.
