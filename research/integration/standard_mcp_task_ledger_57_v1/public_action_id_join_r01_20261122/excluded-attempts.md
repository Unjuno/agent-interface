Initial attempt: new completed-action test assumed the inherited synthetic dispatcher event already had a different recorder ID; setup used `a…a` for both IDs, so the test failed at its inequality precondition. Corrected the synthetic recorder ID to `d…d`.

A second test-authoring attempt placed a recovered-path assertion before the local reconciled receipt assignment; it failed with `UnboundLocalError`. Moved the assertion after reconciliation and used recorder ID `f…f` while the public action body retains `a…a`.

These were test fixture/order defects, not exercised production failures. Corrected final verification is retained in `combined-normal.log` and `combined-optimized.log`, 68/68 in both modes.
