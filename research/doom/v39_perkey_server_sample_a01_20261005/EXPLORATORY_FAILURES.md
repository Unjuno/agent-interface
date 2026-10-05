# Exploratory setup outcomes

These were test-runner or scratch-mirror setup problems, not candidate behavior results.

- Initial compatibility test invocations could not import modules omitted from the scratch mirror (executor_v13, executor_v3, lease.py, executor_v5, lease_cause_v1/v2, lease_release_v1, and pinned regression modules). I fetched the exact referenced current-main files, checked their Git blob identities, and reran the suites. Final normal and optimized runs passed.
- A first raw-source identity fetch used a wrongly escaped Git object header, so it rejected executor_v3.py before writing it. The hash routine was corrected to use the Git blob NUL separator; every later downloaded dependency matched its pinned blob.
- The first draft of the negative-control test passed a Boolean where its one-shot failure counter was indexed, causing fake samples to be reported unavailable. The harness now normalizes Boolean input into a one-shot list; the query-error case then injects exactly one OSError and the ordinary candidate case passes.
- The integration test was not considered passing until these harness issues were corrected and the exact-source runs were repeated. No test or experiment result has been relabeled as live evidence.

