# Issue #4824 — online correction retention/forgetting

## H/T/D/C/U

**H.** A single rank-2 output LoRA adapter can absorb eight sequential single-row
skill-B corrections after a frozen skill-A base while retaining skill A. The
decisive quantity is the joint held-out A/B curve after each update; unknown
scope and stale epoch must yield before model execution.

**T.** One deterministic local Docker CPU allocation on the exact cached image
`needle-pilot05:local`, ID
`sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`,
linux/amd64. CPython 3.12.14, PyTorch 2.5.1+cpu, one PyTorch thread. Three
predeclared seeds 68117, 68229, 68341. Each uses 8 binary inputs, hidden-16
tanh, four outputs; skill A is always class 0; skill B is class 1 iff feature
0 is 1. Each seed uses a 16-row support set balanced on feature 0, independently
generated 256-row balanced held-out A and B sets. Train the base for exactly
400 full-support AdamW steps (lr .03, weight decay 1e-4). Freeze base tensors;
train one rank-2 output adapter for exactly eight sequential corrections
(support rows 0..7, one AdamW step each, lr .04, weight decay 1e-4, batch 1).
Evaluate at step 0 and after each arrival. Fixed seeds, data salts, architecture,
order and hyperparameters are in `runner.py`; no replay, extra epochs, tuning,
replacement seeds, retry, GPU, image pull, install, network or input emission.

**D.** Scoped PASS requires every seed's final A and B accuracy >=.90, all
intermediate A accuracy >=.90, exact independent logits/metric reconstruction,
unchanged frozen-base digest, 9/9 unknown/stale YIELD per seed, all audit
controls rejected, and zero audit errors. B>=.90 with any post-update A<.90 is
`FAIL_ONLINE_CORRECTION_FORGETTING`; valid integrity but any final B<.90 is
`FAIL_ONLINE_CORRECTION_NO_ACQUISITION`; otherwise `HOLD_THRESHOLD_OR_VARIANCE`.
Identity, environment, source, or audit defects are STOP, never a model result.
Only one formal training invocation and one separate read-only-source audit.

**C.** The task is intentionally synthetic and simple; B shares class 0 with A
on half its rows. This tests a narrow online-correction boundary, not realistic
skill learning. Unknown-scope YIELD is deterministic wrapper behavior, not
learned OOD detection. Construction checks (`construction.py`) execute no
optimizer updates and are excluded from formal evidence.

**U.** No natural language, vision, Astra demonstrations, GUI/task effects,
distribution transfer, concurrent inference, restart durability, realistic
forgetting rate, production latency/safety or action authority claim. All routes
remain proposal-only (`authority=false`); model calls are not input emissions.

## Reproduce

The formal output directory must be fresh. Mount source read-only and output
read/write. Use no network and no GPU:

```bash
docker run --rm --pull=never --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=512m --memory=2g --cpus=1 \
  --pids-limit=64 --security-opt=no-new-privileges \
  -e PYTHONPYCACHEPREFIX=/tmp/pycache -v <source>:/src:ro -v <fresh-output>:/out:rw \
  --entrypoint python3 needle-pilot05:local /src/runner.py
```

Then run `audit.py /out/formal/raw.json --output /out/formal/audit.json` in a
separate container with the same image and source read-only. The auditor imports
neither the runner nor its functions; it independently regenerates the inputs,
recomputes every held-out logit and metric from retained base/adapter tensors,
checks all scope controls, and tests 11 corruptions. The local construction
block passed 12 assertions with zero optimizer updates. This is separate from
the formal outcome.
