# Post-restart local integration checks

Both native integration-check suites passed. Protocol: 251 tests. Harness: 106 tests.
The archive retains complete logs, result metadata, and the exact guarded implementation
and relay/test sources. The relay discovery test now checks that all advertised public
tools are covered by its explicit allowlist, in addition to actual SDK forwarding of
the batch tool and rejection of malformed references before backend initialization.

This is contract evidence, not completed live GUI or speed/token evidence. The interrupted
primary allocation is preserved separately in ../guarded-mint-many-interrupted-01.
