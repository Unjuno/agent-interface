# Mitra-v2 GPU resident-path successor (#4745)

This package is a new, additive successor to the immutable CPU STOP in #853. It
reuses the exact #853 synthetic support/query fixture and pinned model snapshot.
It does not edit or rerun the consumed CPU allocation.

The formal runner directly uses AutoGluon's `MitraClassifier` with an explicit
CUDA device and `fine_tune=False`; it retains one classifier/trainer/model for
all single-row predictions. It records a per-call CUDA event, resident CUDA
parameter bytes, GPU allocator bytes, process read-counter delta, wall latency,
raw six-class probabilities, and query timestamps. A separate standard-library
auditor checks the raw result without importing torch or accessing a GPU.

Current construction checks establish Python 3.11 / Torch 2.5.1+cu121 package
resolution and Mitra module import only. They have not loaded the checkpoint,
called `fit`/`predict_proba`, allocated the GPU, or established CUDA forward
compatibility. Issue #4738 has completed, but Issue #4754 is a newer open RTX
3080 allocation; formal model execution is prohibited until all GPU owners are
complete and a fresh collision audit clears the device.

`requirements.lock` contains only resolved additions to the immutable pinned
base image, `wheelhouse-manifest.json` inventories all local downloaded wheels,
and the formal image build consumes both with networking disabled.

