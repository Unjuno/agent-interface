# Corrected Xdummy native XKB round-trip freeze

Task `XKB-XDUMMY-MAP-ROUNDTRIP-20260916-002`, Issue #387.
BASE `a890afb391ad1aa99b29bb45493fa4d11c0da79c`.
No scored server has run under this task at publication of this freeze.

Only two predecessor harness defects change: runner-process DISPLAY/XAUTHORITY propagation and typed HARNESS_FAIL finalization. Xdummy invocation, displays :180/:181/:182, German resolved SHA, XKB load/readback gates and zero-input contract are unchanged. No new X-server construction occurred after Issue #387; only py_compile and a synthetic no-server typed-harness audit test passed. The exact diff is reconstructible from the retained v1 and v2 source blobs; no unretained patch artifact is part of the freeze.

Source SHA-256:
- `run_arm.py` `d1d238211dad83a62883596912f921a2a3c58a1cc4610e45c389d2361c3efbf2`
- `run_block.py` `d948d3aa6c20984381fcbde852b8040740e7afb6d763f141581488610d3dbaa7`
- `audit.py` `04cd8fb22764ff4dca6c1c40392d47f25e4c3dbf495070f419cd7da6affa902a`
- `test_audit.py` `77d61ff9cbe18477a6858bf350dbf1e9d1f678c61d7a02383b960d4006971baa`
- `plan.json` `ab8f37b0a71e75422e0fd5526e1b88e3d45d504d33840f5a8904cd410470d6b0`
- `environment.json` `922a3ea88bba25645d5dc97c660f703e6677f0e39710405dc77f039049a3b8a8`
- `prereg.json` `0d605178691901ddda847efec6bf43f9d43a6b86c362d8b18943096df321d36b`

Formal: exactly three fresh Xdummy/Xorg servers, zero XTEST/Tk/key/task input. PASS requires all three to expose changed live server/core state after native German load and full-XKB AD01 third symbol `at` with RALT `ISO_Level3_Shift`. Typed setup/harness/integrity outcomes remain distinct. No rerun or projection fallback.
