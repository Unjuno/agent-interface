# Formal report — Issue #4567

**Disposition:** `FAIL_HELDOUT_COORDINATE_QUALITY`  
**Independent audit:** PASS; zero integrity errors  
**Formal allocation:** one local RTX 3080 invocation; no retry

## Result

| Arm | Held-out examples | Exact coordinates | Schema/bounds valid |
|---|---:|---:|---:|
| Narrow | 240 | 0 (0%) | 240/240 |
| Broad | 240 | 0 (0%) | 240/240 |

All four held-out broad template families scored 0%. Broad-minus-narrow exact accuracy was 0 percentage points. The 6 models used 3,000 optimizer updates in total; wall time was 10.4336 s and peak CUDA allocation was 97,987,072 bytes.

Raw results and independent audit are retained in [results/formal01](results/formal01/). Their raw-byte SHA-256 values are recorded in [FREEZE.json](FREEZE.json). Construction, GPU-occupancy snapshots, command summaries, and exact source are retained beside them.

## Interpretation and scope

The fixed training recipe did not achieve held-out coordinate transfer on this reused synthetic raster corpus. Schema validity alone did not imply correct coordinates. This does not establish that template diversity is generally ineffective and is not real-application or GUI evidence. No post-result tuning, rerun, GUI input, or action authority occurred.

The canonical frozen allocation remains on its original branch and PR #4578. This path-disambiguated snapshot exists because an earlier #4561 study had already occupied the same historical directory name on main. See [INTEGRATION_NOTE.md](INTEGRATION_NOTE.md); all allocation files reuse their original Git blobs unchanged.
