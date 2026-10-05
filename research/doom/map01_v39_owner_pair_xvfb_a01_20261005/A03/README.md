# A03 result: shared-display release under the V39 owner chain

A03 confirms the preregistered condition on one private Xvfb server using the exact vendored PR #7974 head `c896362a40a1abb279d95e338fe7dfb52a7ee1be`. One-owner control produced server keymap `false → true → false`. With two distinct owners and leases holding W, the server keymap was `false → true → true → false → false`; after A's verified `up`, B still listed keycode 25 in its process-local `owned_keycodes`. B's own later `up` was verified, and final server state was neutral. Candidate and frozen auditor each ran once and exited 0.

This is direct evidence that the tested XQueryKeymap-confirmed release receipt describes shared X-server/device state, not an owner-isolated hold: one owner's KeyRelease can clear the server-global state while another owner retains a local hold. It supports requiring exclusive-display ownership or a cooperative arbiter before interpreting such a receipt as owner-specific. It does not show a production display race or any physical, GUI, or game effect.

The candidate source was frozen at PR #7974 head `c896362a40a1abb279d95e338fe7dfb52a7ee1be` on main `d9bb339b0ba9285cdef57fc347437d25e5943ef1`. PR #7974 advanced after the run and now uses `up_batch`; A03 invokes single-key `up`, so that newer batch operation remains untested here. A03 does not satisfy the live threat-control or MAP01 gate.

Raw output: `results/A03/raw.json` (SHA-256 `579a22672ac58a00f4d52ce80f64fc2e189411fc871fa9f943c0ca97f3f91bc7`). Auditor output: `results/A03/audit.stdout` (SHA-256 `fbe8137a9384fd61faf922f765d442390f001318127b11624c75a2844e109f5a`). Output hashes are listed in `results/OUTPUT_SHA256SUMS`. A01 and A02 first outcomes remain preserved in their own folders.
