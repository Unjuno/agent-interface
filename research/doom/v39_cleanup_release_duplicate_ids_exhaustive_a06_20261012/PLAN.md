# A06 finite construction: current main versus PR #8687 cleanup parser

## H / T / D / C / U

**H.** The PR #8687 duplicate-identity repair should match an independently specified fail-closed oracle for every ordered sequence of up to four accepted/terminal event rows over two command IDs and bounded release/token variants; current main should expose at least one false verified-empty reconstruction and order-sensitive collision.

**T.** Freeze current main commit `f185a9059d485a4f8d5a65e9e7f6782897f67eae`, PR #8687 candidate commit `6195600931fa6de4ecf1a5012cb83b549addb5af`, and their exact controller-cleanup source blobs. Enumerate 245,411 ordered sequences (length 0–4) over 6 acceptance and 16 terminal event shapes (22 total atoms). Execute only the exact cleanup-receipt AST region from each frozen source. Compare `input_terminals_complete` and `input_releases_verified_empty` against a separately implemented contract oracle. Group permutations by event multiset and check order invariance.

**D.** PASS if the candidate matches the oracle on all sequences, is order invariant for all represented multisets, current main has at least one false-positive and one order-sensitive identity collision, and source identities match the freeze. FAIL on any candidate mismatch or missing expected current-main counterexample. HOLD on source/provenance mismatch.

**C.** This is exhaustive only for the stated finite event alphabet and length. It does not represent producer scheduling, unbounded duplicate counts, malformed transport streams beyond the listed variants, or external cleanup effects.

**U.** No production duplicate frequency, controller runtime occurrence, physical per-key release, GUI/game behavior, useful feedback, or live threat response is measured. A05's consumed candidate/raw auditor is not rerun; this is a separate construction input space.

## Runtime

Pure Python on the installed Ubuntu WSL distro; no container, Docker Engine, network, model, GUI, OS input, or game. The property is source/parser semantics, so this run does not require a container boundary.

