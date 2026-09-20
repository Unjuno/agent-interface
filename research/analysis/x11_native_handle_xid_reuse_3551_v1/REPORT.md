# XID-reuse stale-alias experiment (allocation 3551)

**Disposition: `FAIL_STALE_HANDLE_RETARGETED_REPLACEMENT`**  
**Independent audit: `PASS_INDEPENDENT_RAW_RECONSTRUCTION`**

This is a counterexample in the pinned experimental `NativeHandleBridge`, linux/arm64 container and private Xvfb fixture. It is not a claim about the promoted/default runtime or production compositors.

## Protocol and observed preconditions

Source snapshot: `49535d91424c3786330ec62e6d621e4e1eaf1c49`  
Image: `sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916`  
Allocation: `issue3551-xid-reuse-formal-01`

p1 (PID 14, start ticks 5052621) was observed, minted as `old_alias` at [109,118], then exited cleanly. p2 (PID 17, start ticks 5052626) was a distinct process incarnation, alive during the test, with recycled XID 2097152 and identical geometry [80,80,240,160].

Before attempting the alias, independent Xlib `GetGeometry` + `GetImage` checks measured each client window at 240×160 (153600 bytes). Both raw pixel buffers had SHA-256 `3b80132900d7ab9ce6a54b7f01b7fa0d345dd50aafb69135b740ae655c3aba0c`; byte equality was true.

## Result

- The single old-alias attempt was admitted and completed.
- Native/backend emissions increased by 3.
- Independent p2 effect property became `[1,109,118]`, exactly the stale alias target.
- A fresh alias minted from p2 was then admitted and completed as positive control: emissions +3; property became `[2,212,118]`.
- Both completed programs had verified empty release receipts. Bridge closed; both fixtures exited code 0; `recovery_required=false`.

The preregistered failure gate is met: distinct process identity, same XID/geometry/pixels, admitted stale alias, positive emission, and independently observed p2 effect, with a successful fresh control.

## Audit and retained evidence

A separate network-none auditor reconstructed the disposition, checked freeze/source-manifest identities, exact retained PNG manifest and pixel identity, cleanup/release receipts, and five corruption controls. The ten PNG files in this run were byte-identical; one representative full-screen PNG is retained as base64 in `identical_screen_capture.png.base64`. (The independent 240×160 window bytes are represented by the two equal hashes in raw.json.)

- Raw record SHA-256: `3e678ebc161b2fa52e7dfa80f23a10eb556cc71e0c0d78ecb1532b11eda0e400`
- Audit SHA-256: `b657fdae455ab658c0432e55da59c231897fe68fe6a977aaed7ad74f92928c3b`
- Frozen manifest SHA-256: `718e2ca7622535bd4a2a4f1ce9b860c4637b6ecf48bfc6dbc5fa7d9724ace024`
- Freeze SHA-256: `dbd9109ec496af938a974d95fd541f90cb71a3f98c6e9017667a0a46514c572f`
- stdout SHA-256: `98a843ade4480f218aac9de9366d00c5272f0a0d990ab4f862bec8a491d99eb1`
- stderr and Xvfb log: empty (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`)

The raw record retains inherited descriptive `issue` / `parent_issue` fields (3534/3530); the unique allocation ID, source commit and frozen hashes identify this run. This metadata inconsistency does not alter the measured sequence or the independently reconstructed decision.

## Limitations

One experimental bridge revision, one X11 server/image and one allocation. No mitigation was implemented or tested. No inference is made about other bridges, default runtime, desktop sessions, window managers or real applications.