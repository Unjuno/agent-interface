# Arena v0 RAW vs GRID80 target-localization rung

This is a paired, model-in-the-loop target-localization first rung for Issue
#4666. It does not run Arena actions or claim full task success. The same v0
seeded target scene is rasterized twice: `RAW` and `GRID80`, which adds 80-pixel
grid lines and small axis labels while preserving source-image coordinates.
Both calls receive the same textual task, model digest, JSON schema, decoding
settings, and isolated one-request context.

## Frozen allocation

See [`FREEZE.json`](FREEZE.json) and [`PROTOCOL.md`](PROTOCOL.md). Formal seeds
are 8866601–8866612 at difficulty 0.35. Seed 8866600 is excluded construction
and warmup only. The treatment gate requires equal-or-better target identity
and Engine-hit counts, at least 20% lower pooled median center error, and a
GRID80 error win on at least 8/12 pairs. A no-gain result is HOLD, not a broad
failure of visual encoding.

Images are deterministic rasterizations of public v0 `TARGET` stage geometry,
not Tk/X11 captures. No GUI input is sent. The runner uses a local Ollama
service at the single literal endpoint `host.docker.internal:11434`; Docker
bridge networking is used because an `--internal` network could not reach the
host service. Network-level egress isolation is not claimed. The runner has no
provider credentials or external URLs.

## Validation and run

From the repository root, use the already-cached pinned `python@` image in
`FREEZE.json`; do not pull or install packages. Run the test suite with
`--network none`, read-only root/source, dropped capabilities, no-new-privileges,
and a bounded `/tmp`. Before formal use, verify the exact host Ollama model tag
and digest and the Docker image ID. The construction pair is retained under
`construction/seed-8866600/`. Formal output is exclusive-create under
`formal/001/`; any incomplete attempt or missing raw binding is a STOP, and the
formal invocation is not retried.

The model-facing request contains only the raster image and target description;
seed, spec, target ID, oracle and score remain in evaluator-side files. The
independent auditor takes only read-only raw files, regenerates expected seed
geometry, validates exact prompt/model/image/request bindings, and scores
responses using the Arena engine's object-hit rule. It does not contact Ollama.

## Limits

One local model digest, one host, twelve paired static target scenes from one
public generator family. This is not a real-time frontier, action/motor result,
held-out composition test, agent-loop benefit, or cross-domain result. A scoped
signal only justifies a separately frozen follow-up rung.
