# STOP — formal invocation 01

Allocation: `gpu-grounding-template-diversity-2912-successor-01`
Issue: #4546
Commit under test: `85bd667118ce5806087f742b0921ac6e5768cea6`
Disposition: `STOP_INPUT_PATH_ERROR`; do not retry this allocation.

## Exact observed outcome

The one-shot formal command was invoked once with `LOCAL_GPU_FORMAL_ACK=4546-one-shot`. It exited nonzero before the first image was loaded and before any model or optimizer step. The output directory exists and is empty; no result JSON, weights, or audit report were produced. The command's Python exception identified the missing path:

```text
FileNotFoundError: [Errno 2] No such file or directory: '.../research/analysis/gpu_grounding_template_diversity_2912_v1/images/T01/v00.png'
```

The frozen manifest stores images beneath `corpus/images/...`; `train_eval.py::load_rows` joined each manifest-relative `images/...` path to the experiment root instead of to its `corpus/` directory. Therefore this attempt contains zero training examples, zero optimizer updates, and no model-quality result. The only permitted formal invocation for this allocation is consumed.

## Independent serialization gate

At the last live check, the separate local #4205 task was still active and preparing its GPU path. The required GPU-idle/serialization condition was not established before this invocation. This is an additional process-control STOP, even though the path failure occurred before CUDA work. Do not launch another GPU workload from this allocation.

## Evidence and disposition

- Preregistered source and corpus hashes matched locally immediately before invocation.
- Construction suite: 7/7 passed; this is construction-only evidence, not a training result.
- Formal result: none; audit: not run.
- GPU formal compute: none observed; the process failed while opening the first corpus image.
- Next work must use a distinct successor issue/allocation, correct the corpus path, repeat readback/hash verification, and confirm no other task is using the local GPU before any one-shot training.
