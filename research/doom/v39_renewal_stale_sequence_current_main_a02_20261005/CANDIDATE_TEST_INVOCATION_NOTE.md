# Candidate test invocation repair

The first invocation passed the hyphenated experiment directory as a unittest module path and failed during import with `ModuleNotFoundError`; no test body ran. The candidate test was then launched directly with `python candidate_test_fc14994.py` and `V39_CONTROLLER_SOURCE` set to the extracted `fc14994` controller snapshot.

