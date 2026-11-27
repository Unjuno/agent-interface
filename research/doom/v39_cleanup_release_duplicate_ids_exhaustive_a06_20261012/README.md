# A06: finite exhaustive check of duplicate cleanup identities

This package compares the exact cleanup-receipt AST slice in current main with the candidate from PR #8687 against an independent fail-closed contract oracle.

## Frozen inputs

- Main commit: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`
- PR #8687 candidate commit: `6195600931fa6de4ecf1a5012cb83b549addb5af`
- Main source blob: `50c63fa83969ed518a91e39c08d1ee52064eb636`
- Candidate source blob: `576d481a3503e8be4d8ceded8a6371b3fe8850fc`
- The independent audit rechecked blob identities using Git's source-path conversion rules.

## Finite input space

The event alphabet has 22 atoms: six accepted rows (two IDs × omitted/lease-a/lease-b token) and 16 terminal rows (two IDs × eight release forms). All ordered sequences from length zero through four were enumerated: 245,411 total. The exact statements that derive cleanup receipt completeness and verified-empty release are extracted from each frozen `ControllerFailureCleanup.__exit__`; no surrounding controller code is run.

The independent oracle rejects repeated accepted IDs and repeated terminal IDs, requires a terminal for each accepted ID, and checks strict verified-empty key/button lists and token consistency when a terminal supplies a token.

## Results

- Candidate: 0 oracle mismatches, 0 order-sensitive multiset profiles, and 0 ambiguous-identity empty-release certifications.
- Current main: 92,690 false-positive verified-empty certifications and 1,118 order-sensitive multiset profiles.
- Independent replay: PASS, reproducing the counts and validating both Git blob identities.
- First simple false positive: two terminal rows both named `cmd-a`; main reports complete and empty, while the oracle and candidate reject the duplicate identity.

Machine-readable outputs are in `results/candidate.json` and `results/audit.json`; the exact enumerator and separately written replay are `candidate.py` and `audit.py`.

## Limits

This is a construction-only, finite parser-semantics result. It does not measure producer timing, runtime frequency, malformed streams outside the alphabet, physical input release, GUI or game behavior, feedback usefulness, or live threat response. It does not establish end-to-end computer-control success, and it does not rerun the previously consumed A05 allocation. No production code is changed by this evidence package.
