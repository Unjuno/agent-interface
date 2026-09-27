STOP_SETUP_OR_INFRA — stale image provenance

The attempted construction command failed before game initialization because
the pre-existing local image tag `agent-interface-map01-clock-review-fixed:20260920`
did not contain `/opt/phase-probe/Dockerfile`, which `runner.py` hashes during
preflight. No raw file, game session, or scientific row was produced. The
container log is retained unchanged. Recovery was a new additive image tag
built from the repository Dockerfile; see construction-clock-25/26.
