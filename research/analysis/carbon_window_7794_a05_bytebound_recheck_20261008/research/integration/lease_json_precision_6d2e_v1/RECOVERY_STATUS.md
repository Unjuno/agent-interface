# Recovery status: partial retained archive (#4435)

Disposition: `HOLD_PARTIAL_ARCHIVE_5_OF_20`.

This recovery preserves the exact eight files present on the original remote
branch, including the five published base64 fragments and the original
`verify_bundle.py`. In a network-disabled, read-only Linux/arm64 CPython 3.13.5
container, each available fragment decoded as valid base64. The available
fragments are exactly `evidence.part00.b64` through `evidence.part04.b64` and
decode to 61,440 bytes total. This is only a fragment-integrity check; archive
reconstruction, archive hash/size verification, extraction, tests, and formal
result audit were not run because required parts are missing.

The original README/verifier describe a 20-part archive. Parts
`evidence.part05.b64` through `evidence.part19.b64` are absent from the source
branch. The stated expected complete archive is 234,064 bytes with SHA-256
`c7de104f6f57948540cd9bc27532193eac0f3c8e88bdabf2c8acbc3b70c6967d`; these
are published expectations, not values reproduced by this partial recovery.
Read-only inspection of the available local Git history/refs and the source
branch's GitHub Actions runs found no missing parts or downloadable workflow
artifacts. No claim is made that all possible external copies were searched.

The source README reports one consumed formal allocation with 1,062 rows and
an issue-scoped PASS. Its reported raw SHA-256 is
`624d2b6434d2614fdb5d7001bec7b48904dc722fe1cf2e021a3e5673e6d357ba`, but the
raw result and audit package were not recovered here. Preserve that disposition
as historical, unverified evidence; do not rerun, replace, tune, or infer the
formal result from these five fragments. A complete archive copy or explicit
missing-part provenance is needed to resume evidence validation.
