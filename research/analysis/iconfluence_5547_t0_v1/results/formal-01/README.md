# Formal-01 audit history

`RUN.json` and the captured Docker console are the first pass: candidate exited 0 and the initial, incomplete auditor reported PASS. A stricter independent post-run review over the exact same raw candidate output then checked idempotence and correctly changed the scientific disposition to FAIL (`audit.json`). The initial audit did not test same-delta quota idempotence. No candidate rerun occurred. The review is a separate audit of retained bytes, not a second allocation.
