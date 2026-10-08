# #1522 A2 direct-ROI batched translation characterization

Direct predecessor #1495 stopped without a scientific characterization result because its frozen harness generated full 256x256 noisy canvases even though the detector consumes only a fixed 48x48 ROI.

H: direct generation of the same iid Gaussian 48x48 ROI distribution preserves the detector science and makes the 75-cell/1000-pair characterization executable.

T: preserve every #1495 detector/geometry/noise/gate constant. Excluded construction requires exact sigma0 geometry and scalar-vs-batched identity on identical supplied noise arrays. Fresh characterization seed 149520260918002; 3 directions x25 distances x2 classes x1000 pairs; one invocation/reruns0.

D: same #1495 FPR/FNR applicability gates, plus representation/source/audit integrity. Execution stop yields scientific NONE without rerun.

C: RNG stream differs from #1495 but declared ROI distribution is unchanged; clipping/batching bugs are construction-gated.

U: synthetic applicability only; no X11/capture/task/model/human-tempo/production claim.
