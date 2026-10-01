# Cross-platform input reproduction — post-formal clarification

The frozen runner and auditor accept the corpus path as an argument. For a clean Linux checkout, point that argument at the retained exact Windows-form corpus at `corpus_source/corpus.jsonl`; do not rely on Git's canonical LF predecessor checkout. Its SHA-256 is `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`.

Example for a future independent reproduction (it is not a rerun of the retained allocation):

```sh
PKG="$PWD/research/system1/typed_readout_decision_equivalence_1014_v3"
MODEL="/path/to/Qwen2.5-0.5B-Instruct/7ae557604adf67be50417f59c2c2f167def9a775"
IMAGE="sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261"
CORPUS="$PKG/corpus_source/corpus.jsonl"
printf '%s  %s\n' 85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c "$CORPUS" | sha256sum -c -
docker run --rm --gpus all --network none --read-only --cpus 2 --memory 8g --pids-limit 64 \
  --tmpfs /tmp:rw,size=256m \
  --mount "type=bind,src=$MODEL,dst=/model,readonly" \
  --mount "type=bind,src=$PKG,dst=/work,readonly" \
  --mount "type=bind,src=$CORPUS,dst=/corpus.jsonl,readonly" \
  --mount "type=bind,src=$PKG/formal,dst=/out" \
  --entrypoint python "$IMAGE" /work/formal.py --model /model --corpus /corpus.jsonl --out /out/FORMAL_REPRODUCTION.json
```

This command describes the available clean-checkout path; it has deliberately not been run as part of this post-formal provenance fix. Formal run `FORMAL_001.json` and independent audit `AUDIT_001.json` remain the sole recorded allocation and audit.
