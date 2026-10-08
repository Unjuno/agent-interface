# Native XKB map round-trip freeze

Task: `XKB-NATIVE-MAP-ROUNDTRIP-20260916-001`; Issue #372.
Publication BASE: `5a5b748c554fd5e28958a70c750d7fe3dafc65d3`.
No scored arm has run at publication of this freeze.

Exact formal: 3 fresh authenticated `xvfb-run` servers; zero XTEST/Tk/key input. Each arm resolves installed German XKB, requires SHA-256 `3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd`, loads that full resolved map with `xkbcomp -w 0 de.resolved.xkb $DISPLAY`, then reads back `setxkbmap -query`, python-xlib core/modifier map and `xkbcomp -xkb $DISPLAY -`.

Decision: PASS only if all arms show XKEYBOARD, exact resolved hash, exit-zero load, changed server dump, changed core map and AD01 level3 `@`. If integrity/load exit gates pass but live German level3 remains unavailable, return `SETUP_BLOCKED_NATIVE_XKB_APPLY`. No direct core-map projection or task input is allowed.

Source SHA-256:
- `run_arm.py` `703b81bb24d219d65b8d1c66275488ab003d5b619052e3afa2be2a1f0782d5fc`
- `run_block.py` `25f6e21248c0028af5425e2e56bb5f93ffef95e0e0aba4915fcca6c68ff84021`
- `audit.py` `f9d183e11c2e5d7f219d6b6d9996298bbc600fe33e5fd56251c349cd1d61bcac`
- `test_audit.py` `76e859a18263abf5f53bd46110c0b973b29e8c6c93cd6a756471444aadae0ceb`
- `plan.json` `d7da349e3190f0c6db9e5545a25fd3a1b9dd34166bf2fbbaa4474a44165544f2`
- `environment.json` `9e8cd3bdaf86c52461fe2f67eb8e9f081ab31169471eb5323a48756e01c00048`
- `prereg.json` `363beefa56c14210d626a5cac309fa9fb666649f35ccc769a920ef47f3875c35`

Excluded construction is recorded in prereg.json. One first attempt failed because `xmodmap` is absent; later input-free construction established the exact load/readback path and one harness check. Construction is not pooled with formal rows.
