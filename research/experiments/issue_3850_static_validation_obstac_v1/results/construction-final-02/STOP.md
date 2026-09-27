# STOP — construction-final-02

No runner row was produced. The pinned Python image has no Python-script entrypoint; passing `/work/runner.py` as the command made the runtime attempt to execute the mounted read-only file directly, which failed with permission denied. The next construction attempt explicitly invokes `python -B /work/runner.py` into a fresh `construction-final-03/` directory. Formal allocation remains unspent.
