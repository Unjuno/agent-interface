# Construction stop — Issue #4623

## H — hypothesis

One shared-prefix KV cache per fixed state bundle can preserve full-prefill
typed-readout logits while reducing whole-bundle GPU latency on one local
decoder.

## T — construction attempted

Successor allocation: `typed-readout-prefix-gpu-1014-v1-20260927`.
Intake main observed at issue creation: `3c256e531ee0ef7d314fecd2c34217360b72c03c`.
While construction was running, parallel research merged additional work to
main; this branch was fast-forwarded to `ce840296143f11116b05b1d8dfb13c2ce9355fe5`
before evidence publication. The Issue contract and prior evidence remain
unchanged.
Model `Qwen/Qwen2.5-0.5B-Instruct` at revision
`7ae557604adf67be50417f59c2c2f167def9a775`, Transformers 5.16.1,
PyTorch 2.5.1+cu121, FP16, CUDA 12.1, RTX 3080 Laptop GPU (16 GiB).
Container base image is pinned to
`pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`.
The resulting local construction image identity and complete package freeze
are in `ENVIRONMENT.json` / `pip-freeze.txt`; model file identities are in
`MODEL_MANIFEST.json` (weights are not committed).

Two pre-freeze construction failures are retained: build attempt 001 found an
incompatible `safetensors` pin; construction 001 found that synthetic leading
spaces made answer code `0` tokenize to two IDs. The dependency and code spelling
were corrected before the scored construction 002. These are setup findings,
not formal model results.

Construction 002 used three excluded bundles and three suffixes per bundle.
Full-prefill vs cached suffix max-vocabulary-logit absolute errors were
0.0869140625 (B00), 0.1083984375 (B17) and 0.103515625 (B63), far above the
preregistered 0.002 absolute/relative tolerance. No argmax changed in those
nine comparisons. Cross-suffix cache isolation and the eight distinct
single-token answer IDs passed.

The independent container audit reimplemented full and cached forwards without
importing the construction runner. It reconstructed all three retained maxima,
relative maxima and argmax counts exactly; `errors=[]` and status
`PASS_RECONSTRUCTION`. The fixed numerical gate is nevertheless **FAIL**.
See `construction/CONSTRUCTION_002.json` and
`construction/AUDIT_CONSTRUCTION_002.json`.

Disposition: **STOP_CONSTRUCTION_LOGIT_TOLERANCE**. The formal 64-bundle,
1,024-timed-bundle-per-arm block was not started; formal timings, semantic
accuracy, and a shared-prefix benefit are unavailable. No threshold relaxation,
dtype change, replacement model, retry, or runtime promotion was performed.

## D — decision

Do not claim a mechanism pass. The fixed all-vocabulary FP16 tolerance is not
met by this construction. Top-answer agreement on nine excluded comparisons
does not override the numerical gate or establish typed operation/target
quality.

## C — alternatives

The observed delta may arise from different FP16 accumulation/attention paths
between full-sequence and incremental cached execution, a cache/position
implementation defect, or both. The construction did not isolate which cause
dominates. The small synthetic subset does not estimate its prevalence.

## U — limits

This is a narrowly scoped construction stop on one model revision, one GPU and
one environment. It establishes neither a latency benefit nor a latency
regression; no timing allocation ran. It does not establish #1015 shadow
capability, semantic accuracy, GUI behavior, action authority, CPU behavior,
cross-device transfer, or a product/SLO claim. Hashes establish integrity only.
