# Formal07 result disposition: STOP_PROVENANCE_OR_RUNNER

The runner completed the frozen one-shot allocation and the independent raw-only auditor returned `PASS_MIDPROGRAM_REMAP_FAIL_CLOSED`. The control saved the exact expected `a_`; both remap rows refused at operation 6 before the second text, with actor exit 0, target layout readback, verified neutral release, and natural Xvfb termination.

The preregistered six-control corruption suite failed its integrity gate: `missing_post_save_wait` returned the clean PASS. The mutation targets the already-refused JP→US row, for which `post_save_wait=None` is the expected state; it makes no change to raw. Therefore the frozen requirement that all six mutations be rejected is not met. Final disposition is **STOP_PROVENANCE_OR_RUNNER**, not a formal PASS. Do not tune this allocation or retry it.

Formal06 separately remains `STOP_PROTOCOL_DEVIATION`; its run predates its freeze. Neither prior allocation is changed by Formal07.

- Raw SHA-256: `CFEDE33BA2C1F8D645E1C66627229B8540C7E81F271E3DBB89AEAF9B5303F55B`
- Wrapper SHA-256: `B7AF4EB0DA7A408AA67DD155CD6B28552FA6858C26485C72C67BC07D590286BC`
- Independent audit: `PASS_MIDPROGRAM_REMAP_FAIL_CLOSED`, no reasons
- Corruption suite: `all_rejected=false`; only the no-op `missing_post_save_wait` control escapes
- Issue freeze: #5236 comment #5923869233
