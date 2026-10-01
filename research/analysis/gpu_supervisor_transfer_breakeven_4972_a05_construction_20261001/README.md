# Allocation-05 CPU construction: unsafe-admission corruption control

## H / T / D / C / U

**H.** A corrected negative control for allocation-03's retained auditor defect should always change a known-safe admission bit from 0 to 1, and should fail closed if no 0 exists.

**T.** Reused the allocation-03 raw auditor with one isolated correction: select the first `cuda_admitted == 0` in the 1,024-row CUDA pair, flip it to 1, and assert a real mutation. A deterministic synthetic candidate was built with 1,024 rows (256 per stratum), all six batch sizes and 30 paired repetitions. No prior candidate raw/timings were used. The construction harness and corrected auditor are retained as `test_full_auditor_controls.py` and `audit.py`.

**D.** Baseline audit returned zero errors. All five frozen corruption controls were rejected: `flip_cuda_hint`, `drop_timing_sample`, `wrong_source_hash`, `duplicate_pair`, and `unsafe_admission`. The committed remote source was fetched back from the branch, placed in a temporary directory, and executed on the Windows host using Python; exit 0 with `PASS synthetic raw-auditor baseline; all 5/5 corruption controls rejected`. The separate minimal helper regression also passed 3/3.

**C.** Local Windows Python; CPU-only synthetic fixtures and temporary files. No CUDA, candidate timing, model, GUI, input, network, container, or live allocation was used.

**U.** Construction-only auditor evidence; it does not validate a real candidate result, consume an allocation, establish CPU/CUDA parity, or claim a crossover. Allocation-03 remains immutable `HOLD_INTEGRITY`. A fresh current-main freeze and exclusive GPU assignment remain required for formal work.

## Reproduction

`python test_unsafe_admission_control.py`

`python test_full_auditor_controls.py`

Expected for the full-auditor test: `PASS synthetic raw-auditor baseline; all 5/5 corruption controls rejected`.
