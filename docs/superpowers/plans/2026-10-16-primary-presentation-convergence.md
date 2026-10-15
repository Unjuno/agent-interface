# Primary presentation failure convergence

**Goal:** Adopt PR8786 without overwriting newer tests; verify post-effect record failure refuses resend and leaves explicit close available in the real exchange/caller modules.

**Sources:** main `d66f53dba6e2aea8de36a345968f9f67f18ec7bb`; PR8786 `5f8fdedaac8fbdaf820ca26dd7ebc7985dc2305a`.

**Architecture:** Preserve old full test and PR snapshot, transplant only its missing test. Add file-effect regressions through actual primary exchange/caller using synthetic host replies for guarded-local/direct-post. Separately retain and read exact file effects, request/reply/presentation and STOP state. No production behavior change unless checks reveal a concrete defect.

**Constraints:** Local Node processes/file fixtures only. No GUI/native/model/provider/WSL/container, no scientific replay. Synthetic release/image metadata is not physical proof. No app task success/economics claim.

- [ ] Adopt original regression and add both-route post-return/partial-effect failure checks, including explicit close and no resend.
- [ ] Run selected host suites, retain full source/conditions/streams and per-cell files; directed missing-STOP control must fail meaningful assertions. Separate saved-only reader rejects contradictory copies.
- [ ] Publish scope, check original/source joins, review immutable patch and integrate. Verify merge before closing PR8786 with continuation, preserve old refs.

The document recovery prototype remains unconnected to full-body/selected-target editor semantics. This narrows failure delivery/custody on an existing supported path, not application recovery or finite physical release.
