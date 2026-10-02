# Issue #5776 v2 artifact integrity audit — 2026-10-01

**Disposition: `FAIL_ARTIFACT_FIXTURE_HASH_MISMATCH`.** This audit does not rerun, revise, or overturn the retained Docker scientific result `FAIL_METHOD_SCOPED`. It tests whether the committed artifact bundle is internally reproducible from its own frozen sources.

## H / T / D / C / U

- **H:** The committed v2 source bundle and retained raw ledger are byte-bound and independently replayable.
- **T:** Fetch main at `ff2164a8b16d386571c91ebba19f6604b4776581`; verify the fixture and raw transport hashes; invoke a local copy of the committed independent audit against the exact committed fixture and expanded raw.
- **D:** PASS only if all frozen file hashes match, the audit completes with zero mismatches, and its stdout exactly matches the retained audit receipt. Any source/raw identity mismatch is FAIL_INTEGRITY and blocks scientific re-verification.
- **C:** Repository content API, git objects, local Python 3.14.5, base64/gzip tooling.
- **U:** This audit cannot determine which fixture bytes were used in the original Docker run, nor recover omitted bytes from a digest alone.

## Observations

Exact main-tree bytes:
- `fixtures.json` SHA-256: `9f332e0300c03c9ac663d6ba7c0af51c0c71a4e12024da0c59655577a5959278`.
- `raw.json.gz.b64` expands to SHA-256 `c9297630b0afc81d34f5f226d88f4c58411399e46d3b80a7ebc7268446a36048`, matching the raw entry in `SHA256SUMS`.
- Expanded raw identifies `fixture_sha256=bdf198224ad6e3c04d789eeeb6f235fdb9da71e505f20ac03bc1fb54182a36d0`.
- `FREEZE.json` and `SHA256SUMS` likewise bind `fixtures.json` to `BDF198224AD6E3C04D789EEEB6F235FDB9DA71E505F20AC03BC1FB54182A36D0`; neither matches the committed fixture file.
- The committed audit's first fixture-identity assertion fails against the exact main-tree files, before replay begins. Its frozen-source hash also differs from the committed `audit.py`: computed `ae16a3336be2335ef44eeadb46da74c35049a369ded0aed35f7956d4f3449c6d`, whereas `SHA256SUMS` records `1E62BB866C43C363E2E76866985AF56647FDC0336323FEB01B4229C0FE9F4B4D`.
- The raw parses as 336 episodes / 40,320 event rows. This structural count does not imply replay validity.

## Reproduction commands and receipts

```sh
git show ff2164a8b16d386571c91ebba19f6604b4776581:research/analysis/recovery_sentinel_5776_t0_v2/fixtures.json | shasum -a 256
git show ff2164a8b16d386571c91ebba19f6604b4776581:research/analysis/recovery_sentinel_5776_t0_v2/raw.json.gz.b64 | base64 -d | gzip -dc | shasum -a 256
```

Observed outputs are recorded in `receipts.txt`. A path-adjusted local invocation of the committed `audit.py` stopped at its fixture SHA-256 assertion with exit 1. This is a construction/integrity failure of the retained bundle; no substitution fixture, source repair, scientific replay, or Docker retry was performed.

## Successor boundary

The original v2 directory and its claims are left byte-for-byte unchanged. Recovering the exact frozen fixture and exact audit source requires locating the original run inputs from an independently retained source; a new rerun would be a new allocation and must not be pooled with the original. Until then, v2's reported replay is not independently reproducible from the merged bundle.
