# WSLc current-main standard-caller recovery R05

Status: **SCOPED FAIL / PRODUCT GATE STILL OPEN**.

The frozen source is current main `26152e5aaebf678d19f2e7431f57b7012a0064b1`; the cached WSLc image is pinned by digest in `conditions.json`. No pull or network access was used. Both attempts ran in fresh ephemeral WSLc containers with the source bind read-only. WSLc warned that the kernel cannot enforce swap limits; the 4 GiB memory setting is recorded as memory-only. The CLI does not expose a read-only-root option.

## Outcomes

- **Normal:** unittest process exited 0. XRes disconnect was observed after 106.99 ms. The release worker returned a verified neutral snapshot and the independent keymap readback was neutral, while the public cancellation envelope correctly stayed `UNKNOWN` / `release_confirmed=false`. The old synthetic task's effect count increased from 1 to 9; a delayed A press was observed, so the independent old-task oracle failed. A fresh session then completed exactly one separately scored task with all keys up and no old-generation input after the new session began; the old cancellation fence remained UNKNOWN. The evidence script's outer `wslc run` returned 2 because its final `exit "$rc"` had a stray carriage return; raw unittest log and inner exit record show the test itself exited 0. Addendum 01 documents this capture defect.
- **Optimized (`-O`):** unittest exited 1. XRes supervision timed out at 504.49 ms, the worker was retired, and owner release was not attempted. Runtime cleanup remained UNKNOWN; the final fixture cleanup read A/B/C up. The full assertion and result JSON are retained.

The result narrows the timeout boundary: 0.5 s was enough in the normal sample but not the optimized sample on this WSLc host. Neither mode establishes old-task success. Physical neutral readback after normal recovery does not change the public `UNKNOWN` status. The optimized run rejects a claim that current main's 0.5 s budget is sufficient across both modes on this host.

## Decision

Do not mark #57 complete or claim product acceptance. Preserve UNKNOWN and deny replay for the old operation. Continue with a separately frozen, one-attempt current-main timing diagnostic to test whether a 1.0 s query allowance advances optimized recovery; even if it does, the old task effect oracle must still be scored and no production bound should be widened from one sample alone.

Run `audit_r05.py` with both `python3` and `python3 -O` from the repository root. It verifies source hashes and the expected evidence classifications; success means the packet is internally consistent, not that the product gate passed.