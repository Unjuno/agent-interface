# Windows checkout repair (#5024)

The original Git tree stored 48 images with a literal backslash after `corpus` in the filename. Windows Git rejects those paths during checkout, before tests can run. They now live below the actual `results/formal01/corpus/` directory.

PATH_MIGRATION.json maps each original path to its replacement and records its original Git blob ID, SHA-256 and size. The images are byte-identical. It also hashes all 21 original non-image files; sources, FREEZE, corpus manifest, results, report and audit remain untouched. No scientific allocation was rerun or rescored, and its disposition is unchanged.

Run `python verify_path_migration.py` from any working directory with standard Python. This checks migrated bytes against both SHA-256 and Git blob identity, and checks every original non-image file. For references inside historical records, resolve the original path via this explicit mapping; do not interpret the old backslash literally on Linux or rewrite the historical records. Historical original paths and bytes remain available at the recorded source_commit. A Linux reconstruction, if needed, can copy each replacement file into a separate directory under its original path from the mapping; the live checkout intentionally uses portable paths.

This verifier establishes retained identity, not a scientific rerun or Windows CI success. Clean Windows checkout and affected build/test validation must be reported separately.
