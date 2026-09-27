# Nested interrupt completion lineage — Issue #4302

Parent #4222 / PR #4278 remains unchanged. Allocation nested-lineage-4302-20260924-n7c2.

## H
A completion counter can mistake duplicate/old/foreign child completion for parent completion. Exact current-stack-top session, id, generation and parent matching should prevent premature root resume. Missing child completion remains unresolved.

## T
Private authenticated TCP-disabled Xvfb and Tk process per case. Actual XTEST a prefix and at most one b suffix. Root target and prefix stay unchanged. Parent/child Toplevels use Tk local grabs. No model, provider, user desktop, task files or experimental network. Explicit supervisor permission covers only synthetic test windows. Policy authority=false means no production authority, not that no test input occurs.

SCENARIOS: NORMAL, DUPLICATE_CHILD, OLD_GENERATION_CHILD, FOREIGN_SESSION, WRONG_PARENT, MISSING_CHILD. Policies COUNT_ONLY_POP and LINEAGE_BOUND_POP. Two fresh repetitions, policy order reversed in rep1. 24 cases total in two immutable12-case batches.

Normal: close C1 and deliver its real receipt; close P1 and deliver receipt. Duplicate: deliver C1 twice before closing P1. Old generation: actually close C1, reopen C2, initialize stack with C2, deliver retained C1 receipt, then C2/P1 real closes. Foreign/wrong-parent: close C1, deliver a copy with session=foreign-session or parent=OTHER:1, then deliver unmodified C1 before closing P1. Missing: close C1 but drop its notification; close P1 and deliver only P1. No timer-based repair, replay or implicit child closure.

Policy sees only its initial frames and delivered receipts, not scenario labels, snapshots or independent app journal. Stack-empty eligibility triggers b to the currently focused Entry, never a direct Entry insertion. The weak comparator deliberately exposes wrong-surface input inside the disposable fixture; it is not current production behavior. Exact focus/application delivery is measured, not assumed.

## D
PASS only if all24 complete: candidate10/10 recoverable root ab, candidate missing2/2 unresolved with zero suffix, candidate wrong0; weak directed wrong8/8; normal4/4 root ab; missing both arms zero suffix; neutral keys/buttons and clean app/Xvfb exits24/24; complete source/raw lineage; separate raw-only auditor errors=[]; >=10 effective corruptions reject. Full contrary behavior is FAIL; unavailable/incomplete evidence is HOLD/STOP. Never interpret app exit as task completion.

Construction may iterate with separate retained records. Freeze exact eight source/environment hashes plus this plan before formal. Formal commands, once each, from this directory:

    python -B run.py --out formal/batch-0 --rep 0 --display-base 1510
    python -B run.py --out formal/batch-1 --rep 1 --display-base 1540
    python -B audit.py formal --reps 0 1 --freeze FREEZE.json --out AUDIT.json
    python -B controls.py formal 0 1

Only run batch1 after batch0 completes. Existing output directories refuse overwrite. Zero scientific retry/replacement/exclusion/tuning. Launcher records actual exit per batch. Source, app raw journals, all controller events, process stderr, row and batch metadata must be retained losslessly. Private ephemeral Xauthority cookies are deleted and never published. Public capsule reproduction checks hashes and audits; it does not rerun formal.

## C
Cooperative receipts are not authentication; directed notifications are not natural race rates. Stable root dependency state, two Tk levels and known event schemas leave deeper/semantic recovery open. No application task completion beyond exact Entry effects is claimed.

## U and integration decision
This is the missing nested-completion correlation boundary of recovery, not promotion of a new runtime. Other agents can combine top-frame receipt matching with #4222 current target/queue/source/result revalidation, then test the composition. No model/latency/token, cross-platform, arbitrary-depth, crash, asynchronous production or global ROADMAP claim.

Roadmap: construction -> public freeze/readback -> two batches -> audit+corruptions -> lossless PR -> exact-head review/CI -> qualified merge and main readback -> owned dependency-safe cleanup. Shared files and old evidence remain untouched.

XTEST semantics background: X.Org XTEST Extension Library specification, https://xorg.freedesktop.org/releases/X11R7.7/doc/libXtst/xtestlib.html. This is virtual X-server input, not physical HID telemetry.
