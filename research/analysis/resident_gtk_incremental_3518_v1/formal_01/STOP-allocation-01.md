# STOP — issue3518-resident-gtk-incremental-01

- Outcome: STOP before first case; 0/32 rows, no GTK/Xvfb process was launched by the runner.
- Command attempted: `docker run --rm --network none ... agent-interface-2972:20260920 python3 /src/runner.py`.
- Observed: exit code 2; `python3: can't open file '/src/python3': [Errno 2] No such file or directory`.
- Cause: this pinned image has `Config.Entrypoint=["python3"]`; the supplied `python3` became its script argument. This is an invocation/configuration error, not a policy or GUI result.
- Integrity: formal_01 source was mounted read-only. Preregistered source hashes remain unchanged. No retry was made under allocation 01.
- Successor: a new allocation ID must preregister the corrected invocation (pass `/src/runner.py` directly to the image entrypoint), preserving this STOP record.
