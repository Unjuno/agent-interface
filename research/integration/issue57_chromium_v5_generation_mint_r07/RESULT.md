# Chromium V5 point-mint generation guard R07

**Disposition: `PASS_CURRENT_MAIN_SCOPED_RECHECK`.** On merged main
`561fe044a2023fc419ed4bc35942272bcbb3c279`, the focused generation-mint and
adjacent handle/caller/core suites passed **23/23 normally and 23/23 under
`-O`** on Windows CPython 3.11.9.

The two negative cases changed only process or window generation while exact
checker pixels, focus, surface, and geometry stayed identical. Both refused
before handle creation. The same-generation positive minted a private-backed
session alias and retained exact patch-digest equality. Raw logs, exit codes,
frozen conditions, source hashes, and the manifest are in [`raw/`](raw/).

This is a post-merge Fake-only recheck of the narrow V5 mint guard. No browser,
X server, OS input, model/provider, live task, or allocation ran. It confirms
the code and regression on current main; it does not bridge the V5 target/evidence
path through adaptive caller v3 or close #57's provider, matched efficiency,
recovery, or reliability gates. See the baseline defect and repair in [R05]
(../issue57_chromium_v5_generation_mint_r05/RESULT.md) and [R06]
(../issue57_chromium_v5_generation_mint_r06/RESULT.md). Keep #57 open.
