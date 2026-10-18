# T0 run outputs

This directory is a distinct writable output mount. `candidate.stdout.json` and `candidate.stderr.txt` preserve the first candidate process output; `audit.stdout.json` and `audit.stderr.txt` preserve the separate auditor process output; `RUN.json` binds their exit codes, hashes, and aggregate fixture counts. Source and frozen fixture are mounted read-only.
