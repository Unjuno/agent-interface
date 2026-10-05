# A07 execution record

- Base: `f2b380c88`; branch `research/8084-diagnostic-threshold-sensitivity-a07-20261005`.
- Interpreter checked before formal attempt: `C:\Users\junny\AppData\Local\Programs\Python\Python312\python.exe`, CPython 3.12.10.
- Construction tests: 3/3 normal and 3/3 under `-O`.
- Freeze staging/commit attempt failed: Git said the A07 paths were outside the sparse-checkout definition. No freeze commit exists.
- Despite that failure, the PowerShell sequence continued and invoked `generate.py` once; exit 0, about 2.4 seconds, 80,000 rows. Output, empty stderr, and generated candidate-input fixture retained.
- Candidate: 0 invocations. Auditor: 0 launch attempts.
- A07 fixture is not formal input and will not be used for a later run. No scientific result.
- No WSLc, Docker, network, model, GUI, GPU, participant, or external data.
