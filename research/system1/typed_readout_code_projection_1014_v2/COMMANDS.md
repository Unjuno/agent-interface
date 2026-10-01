# Commands and execution log — Issue #4639

Both containers used the derived CUDA image ID
`sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`
with `--gpus all --network none --read-only --cpus 2 --memory 8g
--pids-limit 64`, read-only mounts for source, model and corpus, and a writable
result directory. On the recorded host, the model snapshot was
`C:\Users\junny\.cache\huggingface\hub\models--Qwen--Qwen2.5-0.5B-Instruct\snapshots\7ae557604adf67be50417f59c2c2f167def9a775`, and the Git checkout root was
`C:\Users\junny\Documents\Codex\2026-09-19\new-chat\work\agent-interface-research-1024`.
The commands below use PowerShell variables for these paths:

```text
$repo = 'C:\Users\junny\Documents\Codex\2026-09-19\new-chat\work\agent-interface-research-1024'
$model = 'C:\Users\junny\.cache\huggingface\hub\models--Qwen--Qwen2.5-0.5B-Instruct\snapshots\7ae557604adf67be50417f59c2c2f167def9a775'
$pkg = Join-Path $repo 'research\system1\typed_readout_code_projection_1014_v2'
$corpus = Join-Path $repo 'research\system1\typed_readout_prefix_gpu_1014_v1\corpus.jsonl'
$image = 'sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261'
docker run --rm --gpus all --network none --read-only --cpus 2 --memory 8g --pids-limit 64 --tmpfs /tmp:rw,size=256m --mount "type=bind,src=$model,dst=/model,readonly" --mount "type=bind,src=$pkg,dst=/work,readonly" --mount "type=bind,src=$corpus,dst=/corpus.jsonl,readonly" --mount "type=bind,src=$pkg\construction,dst=/out" --entrypoint python $image /work/construction.py --model /model --corpus /corpus.jsonl --out /out/CONSTRUCTION_001.json
docker run --rm --gpus all --network none --read-only --cpus 2 --memory 8g --pids-limit 64 --tmpfs /tmp:rw,size=256m --mount "type=bind,src=$model,dst=/model,readonly" --mount "type=bind,src=$pkg,dst=/work,readonly" --mount "type=bind,src=$corpus,dst=/corpus.jsonl,readonly" --mount "type=bind,src=$pkg\construction,dst=/out" --entrypoint python $image /work/construction_audit.py --model /model --corpus /corpus.jsonl --record /work/construction/CONSTRUCTION_001.json --out /out/AUDIT_CONSTRUCTION_001.json
```

The concrete local cache/output paths were host-private mount sources. Both
processes completed successfully; construction disposition was
`STOP_SELECTED_CODE_TOLERANCE`, and the independent reconstruction had no audit
errors. No formal command was issued after the frozen gate failed.
