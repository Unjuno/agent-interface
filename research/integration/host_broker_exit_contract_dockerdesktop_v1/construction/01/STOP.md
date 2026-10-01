# Construction 01 — STOP

**Classification:** `STOP_CONTAINER_TEST_IMPORT_PATH`.

Docker Desktop started the construction container with the study mounted at `/study` and the runtime source at `/source/runtime`. Before running the fake child or broker, importing `test_contract.py` evaluated `Path(__file__).resolve().parents[3]` as the eager default argument to `os.environ.get`; `/study/test_contract.py` has fewer than four parents, so Python raised `IndexError: 3` even though `BROKER_REPO_ROOT` was set.

The container exited 1. No broker invocation, fake child process, model/provider call, GUI, input, or formal allocation occurred. The formal result path `formal/dockerdesktop-20260926-01/` remained absent. The harness path initialization has been corrected; any continued construction uses a new directory and must retain this STOP unchanged.
