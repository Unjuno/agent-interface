# Issue #6169 duplicate audit packet — preserved, not promoted

## Disposition

This archive retains the exact nine-file package from closed Draft PR #6172,
source head `122cc94c411fa4e7715b7c81b3f7c4b0e22b6dd1`. PR #6172 was explicitly
closed as redundant after PR #6171 was identified as the integration candidate
for the same six frozen inputs. PR #6171 merged to main as
`ded336bb3dbc1b01cc40be658be5a302965c91fb`.

The #6169 owner recorded that their separate inline audit printed a scoped PASS
but the exact source was not captured/hash-bound at invocation. The later
committed auditor in this packet therefore does not authenticate that earlier
execution. Its `audit_result.json`, `RUN.json`, source, and tests are preserved
as historical artifacts, not promoted as a source-bound independent result.
The stronger source-bound #6171 package remains the integration/reproducibility
record; these outputs must not be pooled or substituted for it.

No archived auditor, downloader, or test was executed for this rescue. The
original branch and closed PR remain immutable history. This archive exists to
retain its exact files before removing the stale remote branch; it does not
change Issue #6169's allocation record or claim a MAP01/live-control result.

## Byte identity

`MANIFEST.json` lists the original source path, Git blob, byte count, and
SHA-256 for every preserved file. Static verification found exact identity for
all nine files. The source freeze and historical execution-source limitation
remain verbatim.

## Distinct evidence

- PR #6171 is the merged, source-bound audit successor for the same six inputs.
- PR #6172 was closed as duplicate and states that its inline execution source
  had not been captured at invocation.
- The original #6164 predecessor's FAIL_AUDIT and raw inputs remain unchanged.

These are separate provenance records. This package neither regrades the
predecessor nor validates a scientific hypothesis.
