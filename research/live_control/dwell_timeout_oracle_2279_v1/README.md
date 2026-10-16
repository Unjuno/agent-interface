# Dwell-timeout oracle successor to #2279

H/T/D/C/U

- H: a right-censored dwell is an interval of possible completion times, not a completed event.
- T: with a trusted finite upper bound M, compute the feasible mean interval and exhaustively check a unit grid of censored completions.
- D: one three-observation fixture, one malformed-censor control, exact source hash, and independent audit.
- C: analytical/container-only contract evidence; no live GUI, model, network, latency, token, or task-success claim.
- U/STOP: this does not validate M, censoring mechanisms, or a runtime timeout policy. A future live successor must independently measure those boundaries. The parent #1895/#2279 evidence remains unchanged.

The finite fixture has completed durations 2 and 7, plus a censor at horizon 5, with M=10.
The identified mean interval is [14/3, 19/3]. A censored observation never becomes completion.

Reproduction:

    python audit.py
