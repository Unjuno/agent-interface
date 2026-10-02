# Final local validation of the primary stdio candidate

Validated commit: 8d81a1e8499d04d95128a0842bb48ace61d2846d.
Environment: WSL 3.0.1.0, Ubuntu 24.04.4, Python 3.12.3, Node 24.13.1.
Hosted workflow selects Node 22; this local run does not attest that hosted environment.

180 Node contract tests passed (research relay tests plus every host test).
The shared native integration runner passed 374 protocol and 176 harness tests,
including nine portable distribution tests. Full logs and runner result are retained.
These are inert contract checks, not another model/GUI experiment.

Offline verification of the existing frozen live and raw-file records also passed.
The live allocation was not restarted. No original record or failure was replaced.
Latest fetched main was 8d6ad7be2; merge-tree returned a clean tree.
The pre-test ancestor scan encountered permission-denied systemd temporary directories;
this was an inspection failure, not a test failure. The root has no AGENTS.md.
