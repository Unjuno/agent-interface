# Journal/state reconciliation

Successor probe for [Issue #8300](https://github.com/Unjuno/agent-interface/issues/8300), preserving the earlier #7949 evidence unchanged.

See `PROTOCOL.md` for hypothesis, test, decision gates, constraints, and scope. Construction tests:

```sh
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

Formal execution is intentionally gated on a recorded SHA-256 freeze in the Issue #8300 discussion. Then run `python3 -B run_candidate.py` once and `python3 -B audit.py` once. Do not rerun either after formal outputs exist; preserve failure evidence and classify it.
