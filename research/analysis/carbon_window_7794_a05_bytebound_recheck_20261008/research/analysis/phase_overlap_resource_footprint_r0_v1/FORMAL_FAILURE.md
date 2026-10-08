# Formal failure retention

The first post-freeze formal invocation stopped before enumeration with `NameError: name 'permutations' is not defined`.

This is retained as `FAIL_SOURCE_MATERIALIZATION`, not as a scientific FAIL. The locally materialized executable did not match the frozen Git source identity: the frozen Git analyzer blob is `d1f1e1200ce3077fa206a2a0ad022dbe3f9dfd48`, while the executed local analyzer had SHA-256 `dae77de90420eb75b556f0446144ebac2c220be0ab219f37f7dc5500436590d7`.

No result rows were produced. The same formal allocation is not rerun. A successor may change only source materialization/import integrity and must use a new task identity.
