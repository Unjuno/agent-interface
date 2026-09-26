# Independent formal-01 audit — PASS

The frozen auditor ran exactly once in a fresh pinned container. Evidence and source were read-only mounts; only a distinct, initially empty results mount was writable. Result: `PASS_AUDIT_CONFIRMED_DIAGNOSTIC`, errors `[]`, auditor container exit 0.

It recomputed all 44 runner-artifact hashes against the actual evidence tree; verified raw SHA-256 `45a7cb25a9854b5ccee6ffbd712e1ade381fb25f5f1041657eec0fac3c7d7604`; rebound source base and runner SHA; re-derived each full core-map fingerprint and per-key symbols from both Xlib captures; checked xkbcomp/query outputs, row commands, layout application, process cleanup, and the German/US disposition gates.

Audit JSON SHA-256: `5a5583a6e0f86b4ddc6f678bd56224b82fd56f03ee8475ba76b9ee9efeee7847`. The audit container stdout/exit record is `container-logs/audit-01.stdout.log`, SHA-256 `409046b0e11d551dbd571959f51ab28885dfa3fb4e02f0d8bc2e11ebbb955a78`.

Combined interpretation remains a private-Xvfb diagnostic only. It does not resolve why the prior formal-02 capture recorded an unchanged core map, and it is not a text-delivery/backend result.
