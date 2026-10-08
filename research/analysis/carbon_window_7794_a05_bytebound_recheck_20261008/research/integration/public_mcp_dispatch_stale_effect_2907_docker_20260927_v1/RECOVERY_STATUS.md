# Recovery status — allocation 02

This archival package preserves the frozen source variants and STOP02 without
relabeling the local runner's emitted result as an accepted formal result.
The runner reportedly emitted `PASS_PUBLIC_MCP_STALE_EFFECT_RELEASE_SCOPED`,
but the source uploaded to the branch before execution did not match the
`FREEZE_V2.md` source digest. GitHub therefore did not bind the executed source
to the preregistration. Treat the observed PASS as unverified for the frozen
allocation; do not promote or pool it.

The exact raw result is not reconstructed here. Allocation 02 remains a
source-publication/provenance STOP. No formal rerun or new Docker experiment
was made during this archival recovery.
