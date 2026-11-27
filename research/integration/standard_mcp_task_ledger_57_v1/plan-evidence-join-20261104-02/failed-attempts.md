# Non-authoritative runner attempts

- Final-09 reuse retry: Docker exited 1 before experiment execution because the requested evidence output directory already existed. See `docker-exit-retry-existing-final09.txt`.
- Final-11: Docker exited 1 after the composition test exposed a test assertion key mismatch: observed mint keys were aliases (`calc_entry`, `calc_save`), while expected keys were role names (`entry`, `save`). No runtime behavior or acceptance condition was changed; the assertion now keys by alias. The failed run's `docker-exit-final-11.txt` is retained; its log was superseded by the final-12 successful log.
- Earlier setup failures (wrong interpreter name, line endings, working directory, reused output directory) are described in `README.md`; they are not counted as experiment results.

