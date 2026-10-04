# Unregistered post-outcome candidate invocation

This file preserves a scratch invocation performed during an independent audit
after the registered T4 candidate and auditor had completed. The command
invoked the frozen `candidate.py` a second time against the original frozen
cases and analyzer, writing to `/tmp/pr7365-independent-replay.json`; the
resulting bytes are retained as [`raw.json`](raw.json).

The exact UTC execution time was not captured. The output records Python
3.12.13. No GUI, X11, input, game, model, provider, GPU, network, container, or
shared allocation was used. The replay does not replace or alter T4's original
`output/raw.json` or `RUN.json`.

This was an extra candidate-script invocation beyond T4's declared
`candidate_max=1`. It is a protocol deviation and must be counted when judging
that limit; the registered one-shot record alone no longer describes all
candidate-script executions. No further candidate invocation is authorized by
this record.

Reproduction command that was actually run:

```sh
python -B candidate.py cases.json source/analyze_map01_direct_retained_input_v1.py /tmp/pr7365-independent-replay.json
```

The printed stdout was:

```json
{"allocation": "OWNER-KEYUP-TIMESTAMP-ORDER-5156-T4-20261004-01", "measurement_ready": [true, true, true, true], "row_count": 4}
```

SHA-256 of `raw.json`:
`1e615ac949315b18d2a91580c2573b451832617f74534995a9dfc338644b23a0`.
