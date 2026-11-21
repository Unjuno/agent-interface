# Raw output custody

All output and status files are stored as base64 to preserve exact bytes across Git newline handling. Run `python restore_raw.py` from any directory; it verifies the SHA-256 of every listed file before restoring it. The 12-test focused output is retained in the ignored local logs; the committed 45-test output includes that suite.
