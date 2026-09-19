# Xdummy native XKB round-trip freeze

Task `XKB-XDUMMY-MAP-ROUNDTRIP-20260916-001`, Issue #380.
Publication BASE `f6822835f46f9f8f015317b0ef63a6fab6eed367`.
No scored arm has run at publication of this freeze.

One excluded read-only construction started Xdummy/Xorg successfully and showed the same German resolved XKB can change live server/core/modifier state, unlike Xvfb. That observation is preregistered and is not pooled.

Formal: exactly three fresh authenticated Xdummy servers on displays :180/:181/:182; no XTEST/Tk/key/task input. Same German resolved SHA and same xkbcomp load/readback semantics as #372. PASS requires all three to expose full-XKB AD01 third symbol `at`, RALT `ISO_Level3_Shift`, changed server dump and changed live core mapping.

Source SHA-256:
- `run_arm.py` `c6cc5a1ac4c8434d4f68706205d7ac6f84dfdbc00316a06ea93e9a2d841007e5`
- `run_block.py` `57cbc808b34589976ad51cd73163238dfa7d2fa8c2e0f1cae2056d60bb032bf2`
- `audit.py` `bff4b2697b5af4a756cfdf3b66d56616c5c33c49fc10c18e34464f164854209e`
- `plan.json` `40e09c0b0ecc0a4a43f93dd45b0eb50eb0948aa029890b8e29d1afa36f5e4d2c`
- `environment.json` `8122a26079eb87eabbcc49c4d7b788e5e512bf6757f066198fc67fd82a507678`
- `prereg.json` `cb60d34bef005ce4c141f5ba41383812e8efabdc449bb4628474dedf4611a294`

No Compose/dead-key/payload delivery or core-map projection is authorized.
