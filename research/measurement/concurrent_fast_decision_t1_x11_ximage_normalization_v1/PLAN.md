# #1426 T1 XImage representation-normalization harness successor

Predecessor #1421 retained `STOP_PROCESS_ISOLATION_INSUFFICIENT` with scientific disposition NONE.

One factor only: normalize python-xlib `img.data` losslessly to bytes. `str` is encoded Latin-1 to preserve byte values 0..255; bytes-like payloads are preserved. The exact #1421 process-isolated harness and frozen #1384 science remain otherwise unchanged. The missing state-transition behavior seen in #1421 is intentionally not repaired here.

Construction: exactly one ACTIVATE18 matched pair / two fresh child processes after source-first freeze/readback and #60 finite lease. First outcome retained; reruns/replacements/tuning0. Formal0.
