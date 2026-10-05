# Issue #8185 epoch-bound capture-to-input transform chain T0

Finite CPU method comparison for the open [Issue #8185](https://github.com/Unjuno/agent-interface/issues/8185). Read [PROTOCOL.md](PROTOCOL.md) for the fixed H/T/D/C/U, outcome gates, runtime limitation, and one-shot boundary. This does not test native input or a live display.

Reproduction of construction and retained result:

```sh
python3 -B -m unittest discover -s research/analysis/epoch_transform_chain_8185_t0_20261005 -p 'test_*.py' -v
python3 research/analysis/epoch_transform_chain_8185_t0_20261005/candidate.py
python3 research/analysis/epoch_transform_chain_8185_t0_20261005/audit.py
```

The candidate/auditor commands are the allocation and must not be repeated. `FREEZE.json` binds the source, protocol and candidate input at the frozen main base. `RUN.json` and `SHA256SUMS` retain invocation and output identities. Oracle truth is not mounted/imported by the candidate code path. Results, including failures, remain additive; no runtime promotion follows this synthetic gate.
