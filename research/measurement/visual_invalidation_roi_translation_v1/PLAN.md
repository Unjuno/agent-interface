# #1495 fixed-ROI invalidation translation envelope

Parent: Issue #104 retained `research/visual_invalidation_discovery_v1/REPORT.md`.

One factor only: permit target translation relative to the predecessor's fixed 48x48 ROI while preserving the 12x12 target, +16 semantic intensity change, sigma=2 jitter, |pixel delta|>=12 rule and >=100 changed-pixel invalidation gate.

H: fixed ROI has a finite, direction-dependent translation envelope. Small permitted translation stays below the invalidation gate; larger translation alone becomes a false invalidation. Relevant +16 change remains detectable.

T: synthetic 256x256 grayscale scene, source target centered in the ROI. Horizontal, vertical and diagonal integer d=0..24. Frozen characterization seed 149420260918001, 1000 pairs/class/cell. Independent formula-based geometry audit checks sigma=0 counts. No threshold/ROI/noise/contrast tuning.

D: retain the scoped envelope only if d=0 sensitivity passes, each direction has at least one safe nonzero d and one >=99% false-invalidation d, exact geometry/audit/integrity pass, and execution contract remains one characterization with reruns0. Report last <=1% FPR and first >1% FPR per direction.

C: translation must be policy-permitted; otherwise motion itself may legitimately invalidate. Noise and contrast are synthetic. No target tracker/revalidation is introduced here.

U: no X11/capture/model/task efficacy/human-tempo/production claim. A repair is a separate successor only after this failure envelope is retained.
