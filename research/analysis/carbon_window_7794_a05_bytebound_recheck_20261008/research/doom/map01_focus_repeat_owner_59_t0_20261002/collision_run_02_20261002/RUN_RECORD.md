# Allocation collision — duplicate run 02 (not formal evidence)

## Protocol disposition

This folder preserves a second candidate/auditor pair that was launched under allocation `ISSUE59-FOCUS-REPEAT-OWNER-T0-20261002-01` after the primary pair had already completed and its result commit existed. It is a **protocol deviation**, not a new allocation, not an authorized replication, and not additional scientific evidence. Do not pool it with the primary result or treat this second matching classification as strengthening the hypothesis.

The primary result was committed as `a2c659eec948a4dd592ef2a06a7ebab8fe54c68b` at 2026-10-02 10:41:36 UTC; PR #6387 merged to main as `32ee821d08ccb27cef49f6554a14df4ae120e137` at 10:45:04 UTC. The duplicate candidate started at 10:43:22.6844461 UTC and the duplicate auditor at 10:44:11.6866525 UTC. I failed to refresh the live PR branch immediately before launching after relying on an older Issue/PR snapshot that still showed candidate/auditor counts 0/0/0. The shared branch had advanced before the candidate started. That missed concurrency check is my error; user permission for one run was not permission to duplicate it.

Allocation-wide actual counts are therefore **2 candidate invocations / 2 auditor invocations**, with one duplicate pair beyond the single allowed pair. The primary `formal_01_20261002/RESULTS.md` remains unchanged as the first valid result; its 1/1/0 is the primary run's count, not the complete allocation-wide count after this deviation.

## Duplicate pair outcome and runtime

The second candidate exited 0 and wrote `candidate/raw.json` (4,320 bytes, SHA-256 `686c8a3fca8eceab5061d10f262cb1c3b5070d725bf827ec561c68b651240d6f`). The positive control saw four repeat KeyPress events; focus moved A→B; owner release was `focus_changed`, verified with an empty keymap; the completed B-reader fence observed zero matching KeyPress before release. The separate auditor exited 0 and independently returned `PASS_OWNER_FOCUS_RELEASE_SCOPED` (`auditor/classification.json`, 94 bytes, SHA-256 `022c0bdcbede2d124e6692e27d078fed18210e3d5ba1bcae54a863a89e7fed80`). The identical classification does not erase the one-shot violation.

Both containers used the exact frozen local WSLc image ID `sha256:865bfbcc86992769ec9b8311a2344b67c664639d96d7cf0d5c407df9c2c500ed`, `--pull never --network none`, and `--rm`. WSLc warned that effective memory/swap cgroup enforcement is unavailable; 512M was only requested. No GPU, CUDA, model, Docker Desktop, real desktop input, game, or user effect was involved. Post-run WSLc inventory was empty. Detailed outputs and exits are preserved in this directory; `SHA256SUMS.txt` verifies each file.

An extra Windows host-Python construction check also failed before tests started because that host lacks `python-xlib` and the package-directory invocation could not resolve the repository import root. It was outside the frozen runtime, required no install, and did not invoke candidate/auditor; see `CONSTRUCTION_HOST_CHECK.md`. The exact frozen pre-formal WSLc suite had passed 28/28 before the primary allocation.

## Containment

No more candidate, auditor, or construction commands will be run for this consumed allocation. This record is kept in a separate additive path so the primary raw files and formal result are not overwritten. Issue #59 and the follow-up PR should disclose the duplicate, correct allocation-wide counts, and leave the broader real-time threat/MAP01 gate open.
