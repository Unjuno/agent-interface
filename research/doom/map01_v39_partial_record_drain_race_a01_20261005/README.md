# Partial owner-release record drain race

## H / T / D / C / U

- **H:** V13 publishes an `owner_release` dictionary before the aggregate pointer/keymap checks finish, then mutates it in place after aggregate verification. If the bridge drains the partial record while a per-key sample is unavailable, the per-key row cannot clear `held`; the later verified-empty update is missed after the bridge advances its record cursor.
- **T:** Freeze the #7805 V13 owner/V2 bridge pair. Admit F8, inject failure on the post-release per-key sample (query 4), and block the subsequent aggregate pointer query. Expire the lease while the owner is blocked so the bridge's `execute()` finalizer drains the partial record. Then return the pointer sample and aggregate keymap, allowing the owner to mark the same record verified-empty. Compare with a V3 bridge candidate that waits for synchronous owner release completion before its final drain.
- **D:** Four deterministic tests pass: a confirmed per-key up clears the V2 bridge hold; the unavailable-per-key-sample case reproduces V2's stale F8 after the owner updates to `verified=true`/`keys_down=[]`; V3's completion barrier observes the partial F8 state, waits for the owner operation, and returns with owner and bridge ledgers empty; V3 cancellation emits exactly one contextual confirmed-up row.
- **C:** This supports a candidate bridge completion barrier for the measured fake-display race. The bridge clears its held set only after the owner's synchronous release operation produces aggregate verified-empty state. The V3 candidate may append an additional verified-empty owner record when the original expiry cleanup already completed.
- **U:** Native Windows CPython 3.12.10 fake-display construction only. No live X11, OS input, GUI/game, task effect, model, recovery benefit, latency, or MAP01 allocation. WSLc inventory did not return while shared WSLc clients were active, so the container route is marked HOLD and the native run is not container-equivalent.

## Frozen sources

- Current main at freeze: `dccf55e264f434ca27f2948fe53be09919047819`.
- PR #7805 candidate head: `8ed40fcbc52a9ffd2da1fa14b9b9b2a22f4111a3`.
- V13 owner blob: `123cd29146e5cf9bfd96f4a749c5d421e34ec1e9`.
- V2 bridge blob: `ee1220cdc3d93d96aa1051c072ca7dceeb59c35d`.
- The copied V39 bridge and v12 fixture files were compared with `git show dccf55e:<path>`; each Git blob ID matched.
- `bridge_v3_candidate.py` is an additive research candidate. It makes a synchronous `owner.call("release", lease)` on cancellation, expiry, or focus invalidation before the final record drain.
- `test_cancel_release.py` differs from the upstream bytes only by redirecting `FIX_PATH` to its package-local candidate directory; the exact upstream file is retained under `upstream_sources/`.

## Reproduction and audit

From this directory run `python run_probe.py` once. The runner refuses to overwrite existing `RUN.json` or `RAW_RUN.log`. It runs the four-test suite and retains the full output. Then run `python audit.py`; it checks test receipts, source/package hashes, the one-line upstream harness adaptation, and the full `SHA256SUMS` manifest without rerunning the probe.

The probe uses a small `executor_v3.py` exception-class seam and the repository's fake Xlib harness. It does not instantiate the complete ExecutorV3 or inherited V39 session-release runtime. PRs #7816, #7819, and #7824 retain separate expiry/composition studies; this result tests the specific mutable partial-record and V39/V2 bridge-cursor boundary.
