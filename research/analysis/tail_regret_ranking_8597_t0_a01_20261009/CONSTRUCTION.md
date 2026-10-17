# Construction and verification

Before source freeze, `python -m unittest discover -s research/analysis/tail_regret_ranking_8597_t0_a01_20261009 -v` passed 3/3 tests. These checks validate the candidate grid and auditor implementation and are not formal-run invocations.

After recording the one-pass formal result, the same package tests are rerun once to verify artifact consistency. No candidate or formal-auditor CLI is invoked by that construction check.
