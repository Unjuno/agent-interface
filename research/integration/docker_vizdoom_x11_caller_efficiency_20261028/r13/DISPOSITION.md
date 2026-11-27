# R13 execution disposition

All four attempts failed before the Python harness entered the game: the LF-only wrapper pre-created each output directory to have a place for stdout redirection, while the harness correctly requires the output directory not to exist. The harness raised `FileExistsError` before creating ViZDoom or sending input. No arm was retried. R14 uses a temporary stdout file under `/tmp`, allows the harness to create its own evidence directory, then copies stdout into that directory after completion.
