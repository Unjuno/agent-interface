# Recovery status for #3442 allocation 01

The original `FREEZE.json` is preserved exactly (SHA-256
`a9dc4bfd1488ab328afd4be0e7a58102a16507d2ca8ffcd8de601e7dafbf3d49`). The
remote branch contains no other files, although the freeze references ten
source/plan/environment/construction artifacts. Those exact bytes were not
found in the branch or current main; they are not reconstructed from hashes.

The Issue's recovery audit records formal count 0 for allocation 01. The
separate allocation 02 was frozen and run later; its Issue record reports a
one-shot 390-row candidate and an auditor HOLD due to the operation-index gate.
That distinct result neither supplies allocation 01's missing package nor
retroactively executes its freeze.

Disposition: `HOLD_SOURCE_PACKAGE_MISSING_FORMAL_ZERO`. No allocation was run
or altered during this recovery. This preserves the old commitment and missing
package state, not a scientific result; #3442 remains open.
