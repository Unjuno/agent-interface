# #5329 X11-P01: selected-state evidence compression

## First result

**FAIL_PACKET_BYTE_GATE**, not an overall PASS. Conservative profile retains the four declared predicates on 18 archived native checkpoints and 32 explicitly synthetic states, but native complete canonical UTF-8 packets total 9018 → 7578 bytes (15.968% reduction). The prospective >=20% criterion fails. Synthetic packet costs are separate (10480 → 7904) and cannot subsidize that gate.

Candidate and independent source-reconstructing auditor each executed once in private OrbStack Docker containers. This is a deterministic archived-record consumer experiment: zero new native inputs, no X11/game/model/action-policy execution. The preceding #7041 experiment and first result were not modified or rerun.

## H/T/D/C/U

H: selected-checkpoint profile can preserve owned-F8-up, required-F9-held, whole-keymap-neutral with observed Button1–3 neutral, and scoped receipt verified, with useful packet reduction.

T: four policies over 18 original native checkpoint records plus 32 enumerated synthetic F8/F9/F10/button1/receipt states; 50 records, 200 packets. Freeze precedes the one-shot candidate and auditor. INPUT joins the original raw corpus by whole-file and row SHA256. Candidate mounts only normalized inputs/method; auditor additionally mounts the old archive read-only. Decoder cannot dereference provenance IDs/digests.

D: RAW_CHECKPOINT has zero predicate mismatch. Native RECEIPT_TRUST has 33 mismatches, 6 unknown required predicates, 27 false-positive predicate **values** (not rows, physical actions, or 27 dead owners). KEY_SUBSET has 18 whole-key-neutral unknowns; conservative has zero mismatches/unknowns. Exact separate-family totals and semantic projection collisions are in the immutable runs/auditor/AUDIT.json.

C: a scoped cleanup receipt cannot replace checkpoint state for this consumer. A residual-other-key bit lets the selected profile retain the stated four facts, but did not meet the chosen complete-packet byte target. No actual token, transport billing, latency or product benefit is established.

U: no independently held-out native cohort; these 18 records are from one previously examined protocol. Synthetic states are not native effects. Provenance nonce strings can disclose protocol/arm: this deterministic consumer is not blinded. Collision counts cover semantic payload/keycode/bystander projection, not full-wire aliases; IDs/digests may distinguish full packets. No ideal-decoder Blackwell theorem, information-theoretic lower bound, whole-trace authenticity, owner admission, unknown-key identity, all-button/hardware neutrality, causal diagnosis, model task success, matched recovery or production integration claim.

## Post-run auditor qualification — preserved failure

The frozen auditor uses Python equality for payload/decision comparison. Coherent copied packets substituting a boolean with integer 0/1 passed that check: **2/8 negative controls falsely accepted** in validation/copied_controls_first.json. That first failure and the frozen auditor are unchanged. Do not claim comprehensive adversarial/type validation or eight successful negative controls.

strict_saved.py is a separate post-run read-only qualification, not an original-auditor repair or formal rerun. All original 200 packets pass explicit primitive-type/canonical-metadata checks; both copied type substitutions are rejected. validation/strict_saved.json retains that limited evidence. The prospective byte FAIL remains unchanged. A future production auditor would need stricter typed admission before adoption.

## Reproducibility and integration boundaries

Native source: main merge 675b26e1a8581c29f092ee549a64df779efd26cd, research/concurrency/x11_crash_cleanup_scope_a02_17_5ce3_20261003, raw SHA256 aafcc9a0b9db97619008dbb446304bf8d6ac703616e4a79329111fc674957643. No old-package changes. Method/base d899031e00cdb3707de142590f8a991e1c82832f; exact freeze hashes in FREEZE.json.

Own OrbStack VM research-59-hud-ocr-5ce3-20261003 (01M40FX53D7A1NKSVYYKYDARRZ); cached image sha256:b2ae049f7c500a3f6b6d162b0351297331434cff5a43f66e1bb41aff90478c96. Normal VM shares physical hardware/host mounts: no security or CPU exclusivity claim. Docker was network-none, read-only source/root, own output mount, dropped capabilities, no-new-privileges, 1 CPU/512MiB/128 PIDs. Stage receipts distinguish codec candidate invocations from native input count zero.

Saved-only check: `python3 -B -m unittest discover -s <this-package> -p 'test_*.py'`. Do not invoke consumed run_stage allocations again. Captured local package, workspace and scorer tests are compatibility/construction checks, not new native or model experiments. FILES.json supplies archive hashes.

 Roadmap: this finite allocation is complete with a negative byte result and qualified preservation evidence. #5329 broader evidence sufficiency, canonical r134 per-key native lifecycle/useful feedback and bounded matched recovery, live-game and model/product benefit remain open. Other workers' native app/game/proposer lanes were not taken over.

Local package tests: 14/14 host and 14/14 container; workspace fixtures 21/21, scorer fixtures 2/2. The first saved-test container launcher failed because the image entrypoint already invokes Python; an explicit Python entrypoint corrected that launcher only, without a formal experiment rerun. Both receipts are preserved. The first VM listing used an unsupported --json flag; the documented --format json readback follows separately. Zero running containers were recorded before stopping only the owned VM; retained exited containers/image are recoverable. These operational failures do not alter the scientific FAIL.
