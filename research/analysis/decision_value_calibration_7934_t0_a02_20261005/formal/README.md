# A02 formal outputs

`terminal.json` is the terminal record. The frozen WSLc run started the
simulator once and independent auditor once, producing 4096 observations and
`PASS_CALIBRATION_BOUNDARY` with no retries.

`FORMAL_MANIFEST.json` binds eight gzip-compressed raw-row chunks and the
candidate result to their original byte counts and SHA-256 hashes. It also
binds the exact stdout/stderr streams and terminal record. Run
`reconstruct_formal.py` from the package root to verify the files; this does not
rerun the simulator or auditor.
