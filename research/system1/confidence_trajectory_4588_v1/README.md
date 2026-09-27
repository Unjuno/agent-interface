# Confidence trajectory first rung (#4588)

This directory retains one 84-case deterministic, model-free, authority-neutral
container experiment. Read [PLAN.md](PLAN.md) and `FREEZE.json` before interpreting
any output. This is a synthetic discriminator result, not a live-system or
runtime-promotion result.

The frozen runner consumes only the local fixed corpus generator in `run.py`
and writes a new results directory. The raw-only `audit.py` uses a separately
written reference reconstruction and does not import the runner. It must be run
against a copied result after the sole experiment invocation.

Expected command form inside the image (substitute recorded immutable image ID):

```sh
python -B run.py --freeze FREEZE.json --out /out/formal-01
python -B audit.py /out/formal-01/raw.jsonl --out /out/formal-01/audit.json
```

The exact executed commands, image/platform identity, source hashes, raw hash,
first outcome, independent audit and limitations are recorded in `REPORT.md`.
