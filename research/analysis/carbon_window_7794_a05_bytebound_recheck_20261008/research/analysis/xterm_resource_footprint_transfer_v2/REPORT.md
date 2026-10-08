# #1746 environment hold

The planned exact-Git-checkout materialization stopped before any scientific invocation because the disposable container could not resolve `github.com` during `git clone`.

No fixture/classifier/auditor bytes were materialized from the repository and the classifier was not invoked. The result is therefore `HOLD_ENVIRONMENT`, not PASS or FAIL of the resource-footprint hypothesis.

A successor may change only the source transport: obtain exact file bytes through the already-authorized GitHub MCP, materialize those bytes into the disposable container, recompute their Git blob object IDs locally, and hard-stop unless they equal the frozen identities. Scientific fixture, classifier, gates, and predecessor evidence remain unchanged.
