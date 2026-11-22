# Raw output custody

The final combined 47-test stdout files and run status are stored as base64 to preserve exact bytes across Git newline handling. Run `python restore_raw.py` to verify each decoded SHA-256 and restore the files into `raw/`. The standalone focused suite logs are excluded; the combined run includes them.
