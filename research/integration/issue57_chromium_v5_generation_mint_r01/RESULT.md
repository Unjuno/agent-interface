# Chromium V5 generation-mint R01 setup disposition

**Disposition: `STOPPED_BEFORE_TARGET_IMPORT`; no experimental case ran.**
Normal and `-O` invocations both failed while importing `executor_v3` because
the sibling module `lease` was not on the Python module search path. The
complete errors are retained under [`raw/baseline/`](raw/baseline/). This is
excluded from all product outcomes; R02 changes only import setup.
