# V40 candidate-to-audit identity check (T1, 2026-10-04)

## H / T / D / C / U

**H:** The candidate SHA recorded by the existing V40 construction audit and README identifies the exact candidate source at PR #7586 head `0a86184dfffb16a62e1f39ab87d189e5c6682004`.

**T:** Hash the exact committed candidate bytes independently; rerun the existing structural audit in an extracted temporary tree so its generated `audit.json` cannot overwrite the committed historical record; compare both resulting hashes with the prior audit and README claims.

**D:** `FAIL_SOURCE_IDENTITY` if either committed claim differs from the current candidate bytes. A later PASS requires both claims to match the exact candidate source; it would still establish only provenance identity, not runtime correctness.

**C:** A post-audit source edit can leave a structurally passing result bound to an earlier candidate. Re-running a script that writes `audit.json` in place can destroy the comparison value unless the committed record is first preserved.

**U:** This is a deterministic artifact-integrity check only. It exercises no WAD/parser, model, game, GUI, input, task effect, or live allocation. Hash agreement would not validate candidate behavior.

## Frozen inputs and result

- Candidate: `research/doom/map01_overlap_controller_v40.py` at PR #7586 head above.
- Prior audit: `research/doom/v39_unknown_source_stop_59_t0_20261004/audit.json` (read only; preserved).
- Prior README: `research/doom/v39_unknown_source_stop_59_t0_20261004/README.md` (read only; preserved).
- Independent rerun of the existing five-check structural audit: all five checks passed; it computed candidate SHA-256 `79033d42786d5c1327727dfd57e0cda5e6d08bc9f5f931241c4b4ae4a33f94c9`.
- The committed audit and README instead claim `961eadb2b14d23d9c1f4972addebb58e12553b8667db01a91701f4505dc826b0`.
- Decision: `FAIL_SOURCE_IDENTITY`. The structural checks pass, but their committed result is not source-bound to the current candidate.

## Reproduction

From the repository root, run:

```sh
python3 -m unittest research.doom.v40_candidate_identity_59_t1_20261004.test_identity -v
python3 research/doom/v40_candidate_identity_59_t1_20261004/verify_identity.py
```

The second command is expected to exit 1 while it reports `FAIL_SOURCE_IDENTITY` for the frozen PR head. The verifier is read-only and never rewrites the predecessor audit. `RESULT.json` retains the raw comparison; `SHA256SUMS` binds this successor package.

## Runtime boundary

No container was launched: the private #59 game lane remains unassigned, and the prior OrbStack image probe failed on an unavailable containerd blob. This check only hashes committed bytes and parses two metadata files; it does not require runtime isolation. No image pull, model/game allocation, or retry occurred.
