# Issue #6048 — one-shot strict JSON prompt diagnostic

This is a fresh successor to #5478's one-call output-contract failure. It keeps the already-cached Qwen2.5-0.5B-Instruct checkpoint fixed and tests only whether a stronger output-only prompt yields a raw, fence-free JSON object with exact fields/types. It uses no trie/grammar constraint, adapter, fine-tuning, package install, external inference, network, Docker or WSL.

## H / T / D / C / U

- **H:** One new seeded synthetic evidence summary plus an explicit JSON-only/type prompt yields a contract-valid raw response from one deterministic generation on RTX 3080.
- **T:** One candidate generation with the frozen cached model, input bytes, tokenizer, prompt, `do_sample=False`, and 192-token cap. Candidate process captures CUDA device/allocation, timing, token IDs, raw output and adjacent GPU evidence. Run the CPU-only strict raw auditor exactly once only after candidate exits 0.
- **D:** Pass only on raw JSON/schema validity and recorded one-call RTX 3080 placement. Any malformed output, wrong type, missing evidence, hash/device mismatch or failed audit is the terminal result; no retry, edit-after-result or alternate decode.
- **C:** Local Windows host; no model/tokenizer download, network, container, WSL, package install or fit. The GPU reservation is exclusive 13:20–13:40 UTC as recorded in #5085; exact gates are re-read at start.
- **U:** Single prompt/checkpoint/input; schema compliance is not semantic correctness, general reliability, calibration, or integration evidence.

## Fixed input and CPU construction gate

`INPUT.json` is generated from seed 901734 by `protocol.make_report`. `protocol.py` contains the exact prompt and a strict parser. The CPU-only tests cover valid output, fences, extra text/keys, numeric strings, booleans, nullish-string confusion, unhashable invalid enums and NaN. They are construction checks, not model evidence.

Before source freeze, run only:

```powershell
python -m unittest discover -s . -p 'test_*.py' -v
python -c "from pathlib import Path; [compile((Path(n)).read_text(encoding='utf-8'),n,'exec') for n in ('preflight.py','generate_one.py','audit.py')]"
```

At the exact slot, re-read #5085/#6048/current main, fast-forward this branch if needed, update `FREEZE.json` with the then-current main SHA, and post the source-hash freeze before touching CUDA. Then run `python .\preflight.py` exactly once. If it exits nonzero or `load_authorized` is false, preserve `PREFLIGHT.json`, STOP before model load, and do not repeat it. If it passes, run `python .\generate_one.py` exactly once. If candidate exits 0, invoke `python .\audit.py` exactly once in a separate CPU process. No candidate replay under any outcome.

The local snapshot is `~/.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct/snapshots/7ae557604adf67be50417f59c2c2f167def9a775`; `local_files_only=True` is mandatory. The preflight verifies the model weight digest, tokenizer file manifest, Python/package versions, source/input digests, output collision, C: free space, exact `origin/main` SHA plus `merge-base(HEAD, origin/main)`, RTX identity, compute processes and exact time window without importing PyTorch. The source map deliberately excludes `FREEZE.json` to avoid a self-hash cycle; the freeze and complete source map are recorded in the GitHub issue before load.
