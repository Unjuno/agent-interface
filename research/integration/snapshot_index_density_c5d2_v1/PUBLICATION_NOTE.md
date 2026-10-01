# Publication note — 2026-09-22

This directory is the retrospective GitHub delivery for Issue #4122.

The retained local README and GITHUB_NOTES_DRAFT are preserved as originally staged and therefore correctly say that GitHub publication was unavailable in that earlier session. That statement is historical, not the current repository state.

## Scientific chronology

- allocation `index-density-c5d2-20260922-01` was locally source-frozen before formal execution;
- GitHub public preregistration: **false**;
- formal cases: 9; reruns/replacements: 0;
- result: `PASS_INDEX_DENSITY_MEMORY_SCOPED`;
- the separate demand-index construction stopped before formal execution when #4068 appeared: `STOP_PARALLEL_DUPLICATE_BEFORE_FORMAL`, formal0;
- no old allocation or #4068 result is pooled here.

## Complete raw evidence transport

`DELIVERY.patch` is the exact original patch. Its Git blob must be
`75170152fca0c2b26e87ede43e5334c90ce634a8`.
It contains a Git binary patch for the exact 385,200-byte `evidence.tar.xz`.

Repository-only reconstruction:

```sh
git init /tmp/c5d2-delivery
cd /tmp/c5d2-delivery
git apply --binary <path-to-this-directory>/DELIVERY.patch
sha256sum research/integration/snapshot_index_density_c5d2_v1/evidence.tar.xz
# expected a61bae425120651d662384d8173e1c41602144c701a82c4502565f7a1975207f

cd research/integration/snapshot_index_density_c5d2_v1
python -B restore.py --out /tmp/c5d2-fresh-audit
python -B /tmp/c5d2-fresh-audit/audit.py /tmp/c5d2-fresh-audit
cd /tmp/c5d2-fresh-audit
python -B -m unittest -v test_audit
```

The direct files in this branch are review conveniences. The patch is the lossless repository-accessible delivery of the original complete package, including raw evidence. Do not run consumed formal launchers.

Evidence-only: no runtime/default/workflow/root direction change and no production/model/task/GUI/integrated #57/#2789 claim.
