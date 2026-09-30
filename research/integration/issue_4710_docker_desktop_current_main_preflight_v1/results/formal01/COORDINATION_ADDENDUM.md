# Coordination addendum — parallel formal result collision

After publishing this host's independently audited result, a final GitHub issue read found an earlier report on #4710 (comment `5852496728`) that also labels a different Docker Desktop host's one-shot run `formal-01` and reports PASS. That worker used the preregistered `7e4a...` image, a different CLI, and a different usage/audit result. The two records are distinct host executions; this local package is not a duplicate of their raw evidence.

This means the issue-level allocation's aggregate invocation count is at least two, despite each host reporting one local call. Therefore:

- Local result in this package: `PASS_DOCKER_DESKTOP_CURRENT_MAIN_INSTRUCTIONS_PREFLIGHT_ONLY` (one local call, 45 independent checks, zero errors).
- Issue/allocation-wide disposition: `HOLD_DUPLICATE_PARALLEL_ALLOCATION`; the preregistered single-invocation D condition cannot be certified across workers.

No result is overwritten, deleted, or merged with the other worker's evidence. This PR remains Draft for human coordination/review; do not treat either host's evidence as a replacement for the other. A future run requires a new allocation ID and explicit ownership/one-shot coordination. No further model call was made after discovering the collision.
