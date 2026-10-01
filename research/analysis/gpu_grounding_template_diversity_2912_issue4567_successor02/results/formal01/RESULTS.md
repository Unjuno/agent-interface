# Formal result — Issue #4567

Disposition: `FAIL_HELDOUT_COORDINATE_QUALITY`  
Independent audit: `PASS`, zero integrity errors  
Training allocation: one invocation; no retry

## Outcome

| Arm | Held-out predictions | Exact coordinates | Schema/bounds valid |
|---|---:|---:|---:|
| Narrow, 2 train families | 240 | 0 (0.0%) | 240/240 (100%) |
| Broad, 8 train families | 240 | 0 (0.0%) | 240/240 (100%) |

Broad per-family exact-coordinate rates were T09 0%, T10 0%, T11 0%, and T12 0%. The broad-minus-narrow aggregate difference was 0 percentage points. This fails the frozen quality gate by a wide margin; the schema gate alone passed. No tuning or rerun is permitted in this allocation.

## Compute and integrity

- Local NVIDIA GeForce RTX 3080 Laptop GPU, 16 GiB VRAM; PyTorch 2.5.1+cu121 / CUDA 12.1; driver 581.57.
- Three seeds, two arms per seed, 500 optimizer steps/model (3,000 total), 8,000 sampled examples/model (48,000 total).
- Formal runner wall time: 10.4336 seconds; peak CUDA allocated memory: 97,987,072 bytes.
- Independent audit: 480 unique expected predictions, schema-valid 480/480, exact coordinates 0/480, integrity errors 0.
- Result SHA-256: `c3413348d18d5881d574a3e13f283a261fe2d912ed9e49344d36d54b75fec47a`.
- Audit SHA-256: `b7f141e6222155d31cfb1e17f0a4fc9a1615276f4251e7e111193364254c3d46`.

## Interpretation and limits

The fixed network drove its final sampled training-batch losses low but generalized to none of the four held-out synthetic families. This is evidence against the preregistered model/treatment meeting exact coordinate requirements under this compute budget, not evidence that template diversity is generally ineffective. The corpus is reused, synthetic, and not an independent real-world collection. Exact schema acceptance did not imply coordinate correctness. No output was sent to a GUI and no action authority was granted.
