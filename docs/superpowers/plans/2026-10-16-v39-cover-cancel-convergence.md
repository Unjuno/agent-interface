# V39 cover cancellation convergence plan

**Goal:** Preserve #8384's distinct historical evidence, restore the current
cover-cancellation regression, and characterize its blocked planner boundary.

**Architecture:** Keep the historical source/raw at its original paths and bytes.
Use the current real planner adapter and V39 helper with finite in-process test
substitutes. Do not promote historical construction into live release evidence.

**Constraints:** FINAL v5; Fake X/local only; no producer rerun, provider, WSL,
display, game, container or new model allocation. No new reviewer quorum.

- [ ] Preserve all 15 PR files from pinned head
  `fd52341c4686893ff3de8795c9a5b671c7d20f9c`; verify original blob identity and
  retained checksum references. Read-only audit only after inspecting its source.
- [ ] Retain the first current-main test failure. Repair only the two partial
  release fixtures to the current owner-release schema, preserving assertions.
- [ ] Exercise a failed cover terminal ready while planner interrupt transport
  is held. Record whether the helper inspects it before the transport returns;
  release the test's own gate and confirm refusal, with no input authority claim.
- [ ] Include the repaired/extended test in the isolated local runner. Retain
  normal/-O results and limitations; integrate exact reviewed head/base with CAS.
- [ ] Close only superseded #8384 after preservation and successor merge;
  preserve its author branch and keep #59's physical/recovery gates open.
