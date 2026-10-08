# A01 first outcome

- Candidate command: `python3 candidate.py protocol.json run-01/candidate.json`
- Candidate: one invocation, exit 0; 4 cells, 88 events; stdout digest `32ed5bd0caf9fc81ce2f9c0e9fc90e035196de6982d8655adcbc54ec58dd0991`.
- Auditor command: `python3 auditor.py protocol.json run-01/candidate.json run-01/audit.json`
- Auditor: one invocation, exit 1; no audit output was created. Exact stderr is retained in `auditor.stderr`.
- Failure: the mutation-control loop stored boolean mutation flags and passed a boolean to the raw-output validator, which raised `AttributeError`.
- Candidate and auditor were not rerun. The first raw candidate output and first auditor failure remain unchanged.
