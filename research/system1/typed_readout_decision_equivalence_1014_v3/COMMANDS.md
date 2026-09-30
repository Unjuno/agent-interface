# Exact commands — Issue #4652

The package, model snapshot, and corpus are read-only bind mounts; the nested
`formal/` or `construction/` directory is the writable output mount. The source
branch is frozen before the formal invocation. Construction runs before freeze
and is excluded from all formal rows. CONSTRUCTION_001 was the initial
readiness attempt; after adding an explicit model-file hash check, the final
frozen construction source was rerun as CONSTRUCTION_002.

```powershell
$repo = 'C:\Users\junny\Documents\Codex\2026-09-19\new-chat\work\agent-interface-research-1024'
$pkg = Join-Path $repo 'research\system1\typed_readout_decision_equivalence_1014_v3'
$model = 'C:\Users\junny\.cache\huggingface\hub\models--Qwen--Qwen2.5-0.5B-Instruct\snapshots\7ae557604adf67be50417f59c2c2f167def9a775'
$corpus = Join-Path $repo 'research\system1\typed_readout_prefix_gpu_1014_v1\corpus.jsonl'
$out = Join-Path $pkg 'formal'
$image = 'sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261'
docker run --rm --gpus all --network none --read-only --cpus 2 --memory 8g --pids-limit 64 --tmpfs /tmp:rw,size=256m --mount "type=bind,src=$model,dst=/model,readonly" --mount "type=bind,src=$pkg,dst=/work,readonly" --mount "type=bind,src=$corpus,dst=/corpus.jsonl,readonly" --mount "type=bind,src=$pkg\construction,dst=/out" --entrypoint python $image /work/construction.py --model /model --corpus /corpus.jsonl --out /out/CONSTRUCTION_001.json
docker run --rm --gpus all --network none --read-only --cpus 2 --memory 8g --pids-limit 64 --tmpfs /tmp:rw,size=256m --mount "type=bind,src=$model,dst=/model,readonly" --mount "type=bind,src=$pkg,dst=/work,readonly" --mount "type=bind,src=$corpus,dst=/corpus.jsonl,readonly" --mount "type=bind,src=$pkg\construction,dst=/out" --entrypoint python $image /work/construction.py --model /model --corpus /corpus.jsonl --out /out/CONSTRUCTION_002.json
docker run --rm --gpus all --network none --read-only --cpus 2 --memory 8g --pids-limit 64 --tmpfs /tmp:rw,size=256m --mount "type=bind,src=$model,dst=/model,readonly" --mount "type=bind,src=$pkg,dst=/work,readonly" --mount "type=bind,src=$corpus,dst=/corpus.jsonl,readonly" --mount "type=bind,src=$pkg\formal,dst=/out" --entrypoint python $image /work/formal.py --model /model --corpus /corpus.jsonl --out /out/FORMAL_001.json *> "$out\FORMAL_001.console.log"; $formalExit = $LASTEXITCODE; Set-Content "$out\FORMAL_001.exit_code" $formalExit; Write-Output "FORMAL_DOCKER_EXIT=$formalExit"
docker run --rm --gpus all --network none --read-only --cpus 2 --memory 8g --pids-limit 64 --tmpfs /tmp:rw,size=256m --mount "type=bind,src=$model,dst=/model,readonly" --mount "type=bind,src=$pkg,dst=/work,readonly" --mount "type=bind,src=$corpus,dst=/corpus.jsonl,readonly" --mount "type=bind,src=$pkg\formal,dst=/out" --entrypoint python $image /work/audit.py --model /model --corpus /corpus.jsonl --record /work/formal/FORMAL_001.json --out /out/AUDIT_001.json *> "$out\AUDIT_001.console.log"; $auditExit = $LASTEXITCODE; Set-Content "$out\AUDIT_001.exit_code" $auditExit; Write-Output "AUDIT_DOCKER_EXIT=$auditExit"
```

The stdout/stderr combined console and exact Docker exit code are written to
separate host files. Each formal command is invoked exactly once. A nonzero
process exit is retained; formal output is written before the runner returns
its scientific outcome code.
