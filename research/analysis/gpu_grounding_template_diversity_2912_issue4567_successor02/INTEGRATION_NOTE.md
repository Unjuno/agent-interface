# Integration note — Issue #4567 evidence snapshot

The canonical frozen allocation remains on branch
`research/gpu-grounding-template-diversity-2912-20260927-v2`, commit
`b3c82709687c68a93a5743c58c6624753ea23756`, as submitted in PR #4578.

PR #4574 had already merged a distinct #4561 experiment into the same historical
repository path, `research/analysis/gpu_grounding_template_diversity_2912_v2/`.
The #4567 allocation was created from an older main commit and used that path
before the earlier PR landed. To avoid overwriting either record, this directory
is a path-disambiguated snapshot of the complete #4567 tree. Existing Git blob
objects were re-addressed without changing file contents; `FREEZE.json`,
raw results, audit, corpus images, source, and execution logs remain byte-for-byte
identical to the #4567 branch.

The experiment outcome is unchanged: the independent audit passes integrity,
but held-out exact-coordinate quality fails (0/240 in both arms). The dataset
is reused and synthetic only. This migration does not rerun or retune training.
