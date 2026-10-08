# Primary references

- Python 3.13 time: https://docs.python.org/3.13/library/time.html
  perf_counter_ns measures elapsed time, including waiting; process_time_ns measures
  process CPU time. Clock resolution is not a calibrated error bound.
- Python 3.13 pathlib: https://docs.python.org/3.13/library/pathlib.html
  Path.read_bytes returns file contents as a bytes object.
- Source: runtime/cli_v1/review.py and receipt_image.py at pinned main
  4c701cc51b06296268ad8d9ae3eff1dd6f2d379d, exact blob identities in VENDOR.json.

Documentation was accessed 2026-09-26 JST; installed Python is 3.13.5, while
current versioned web documentation can include later 3.13 maintenance releases.
No claim about the experiment's measured result is inferred from documentation.
