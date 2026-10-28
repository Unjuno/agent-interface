# Docker/Xvfb receipt-retention comparison — R23

## Result

Six counterbalanced matched pairs compared three guarded-X11 routes on fresh ViZDoom FreeDoom2 MAP01 instances. Each arm sent one 600 ms W-forward action. The route timer covers caller entry through route completion; game startup and target-alias minting are excluded from all arms. No model/provider was called.

| Route | n | Mean route latency | Median | Relative speed score* |
|---|---:|---:|---:|---:|
| Direct guarded X11, individual JSON receipts | 6 | 875.531 ms | 875.896 ms | 100.00 |
| Compiled GUI, individual JSON receipts | 6 | 921.742 ms | 920.741 ms | 94.99 |
| Compiled GUI, persistent JSONL journal (current O(1) reference index) | 6 | 871.079 ms | 871.644 ms | 100.51 |

*Score is inverse mean route latency normalized to direct = 100. It is not a model-token, end-to-end task, or human productivity score.

Matched differences: compiled individual-file storage took **46.211 ms longer** than direct on average (median +47.060 ms; slower in all 6 pairs). The journal took **4.452 ms less** than direct on average (median −0.575 ms; 3 wins each), so this sample does not establish a speed advantage over direct. The journal was **50.663 ms faster** than compiled individual-file storage on average (median −47.768 ms; faster in all 6 pairs), a 5.50% lower latency.

## Correctness and evidence gates

All **18/18 arms** passed all six scoped gates: route completion, W-down observed during the call, a verified empty release receipt, independent W-up after return, changed game position, and a successful effect receipt. Every bridge ended with no recovery-required state and no held keys/buttons.

Each journal arm retained 37 unique references and verified its hash chain on open. An independent read-only audit reopened all six journals and resolved all **222/222** references; each post-close terminal reference also resolved. The task-local packet retains raw stdout, per-arm Xvfb logs, host Docker exit codes, conditions, and source snapshots. It is outside this worktree at [`../../../../../private-packets/docker_vizdoom_native_retention_confirmatory_20261029_r23/`](../../../../../private-packets/docker_vizdoom_native_retention_confirmatory_20261029_r23/); its `POSTTRIAL_SHA256SUMS.json` is the file digest index. A current read-only audit verified all 758 indexed files with zero hash mismatches; see [custody audit](custody_audit.json). The pretrial manifest was rechecked before analysis and all entries matched.

## Scope and provenance

This uses the pinned local image `sha256:b473b61c9dda0fab168f4a2118bd1206676dc6913122a3b9193d423426bc0b84`, Linux/amd64 Docker Desktop, a private Xvfb, `--network none`, a read-only container root, and read-only source/control mounts. The journal arm includes a per-record `flush()+fsync()`. It is a narrow one-action route comparison; it does not establish WSLc or native-Windows transfer, MAP01 completion, cancellation/delayed-input recovery, general reliability, or provider-token savings.

The runtime base is `3a615907cbfaa493761c7634502ab451e56678f3` plus the current local, unmerged O(1) sequence-to-hash index change in `runtime/guarded_x11_v1/receipt_journal.py` from `feat/x11-jsonl-retention`. All runtime execution files, runner, wrapper, seeds, and conditions are hashed before the first arm in `PRETRIAL_SHA256SUMS.json`. The measured direct-vs-compiled result covers the bridge/compiled route used here, not the complete public MCP/provider loop.

R22 is preserved separately because it used the preceding linear-scan journal lookup. R20's earlier exploratory timing is also not pooled because its runner changed during that trial. The R21 container-path setup failure is retained in its own packet; it launched no game and sent no input.
