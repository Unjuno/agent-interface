# Current-main port of #7504 batch key-release evidence

## H/T/D/C/U

- **H:** Closed-unmerged PR #7504 measured per-key XTest release request-to-single-batch-XSync bounds during cancellation cleanup. It retained three earlier STOP attempts and one nonformal local Xvfb smoke with seven checks. The historical record explicitly says this is an X-server request/processing interval, not a physical transition or application-consumption timestamp.
- **T:** Preserved the four original run records and README unchanged, plus frozen #7504 source/test snapshots. Ported only the batch cleanup interval capture into current-main V13 `release(reason)`; the V4 transition wrapper/default and explicit-key-up verification path are unchanged. The live regression now restores `sys.modules` around fake-Xlib imports and tests cleanup in the same process.
- **D:** Local Python 3.14.5 in-memory composition of current-main V10/V11/V13 and the ported fixture: 5/5 focused tests passed (two-key cancellation intervals, V11 explicit-up behavior, V13 wrapper relationship, executor event preservation, and module isolation). The original #7504 source also has a retained nonformal Xvfb PASS with three STOPs; that result belongs only to its frozen old source.
- **C:** Each key's request-start timestamp is paired with the return of the existing single batch XSync and published on the `owner_release` record; no per-key sync/query is added.
- **U:** The current-main port was not rerun on Xvfb or in a container; validation was an in-memory source-loaded fake-Xlib test with stubbed executor exceptions/base. This is not full repository CI, physical key state, app consumption, live gameplay, recovery, or MAP01 evidence. Hosted checks are pending.

## Frozen provenance

- Current-main base: `53ec001a334e4077caf665ff56372cd4b0ccb068`; current V13 blob: `f10f2d05dcaa63c35b51c8f38b737753574b8fa0`; V11 blob: `842071284156d3ccc647f47135ee62a9e512cb56`.
- Frozen #7504 source commit: `65b29cf63efad1c66db58e2df29d533045304f03`; `input_owner_v13.py` blob `b590babae510c65fd3e00efaa5196f5ee7f2fd0c`; original test blob `3e2d75e5134220db6caaca0d65f2c3a694a7c7ee`.
- Original Xvfb STOP/PASS run records and their original README are retained byte-for-byte at this directory.