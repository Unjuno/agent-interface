# Issue #4848 formal disposition

## Outcome

`STOP_PREFIX_BYTE_AUDIT_WRAPPER_TYPEERROR`. The one allowed formal Docker orchestration started and stopped before model/base construction. The numeric prefix check (`torch.equal(xc64[:16], xc16)`) had passed; converting a two-dimensional tensor's `tolist()` result with Python `bytes()` raised `TypeError: 'list' object cannot be interpreted as an integer`. No optimizer was constructed or stepped, no held-out scoring ran, and the dedicated output volume remained empty. The signed accuracy delta is unavailable and the H hypothesis is not adjudicated.

The failure is preserved as-is. Seed 7866201 is consumed under the no-retry rule; the wrapper will not be rerun with this seed. A fresh allocation is required for corrected diagnostic work.

## Frozen formal command (executed once)

```text
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount type=bind,source=<scratch>/needle-role-c-support64-diagnostic-4848-v1,target=/src,readonly --mount type=volume,source=unjuno-needle-role-c-support64-diagnostic-4848-v1,target=/out --tmpfs /tmp:rw,noexec,nosuid,size=64m -e NEEDLE_SEED=7866201 -e NEEDLE_OUTPUT=/out --entrypoint python needle-pilot05:local /src/paired.py
```

Captured stderr/stdout:

```text
/usr/local/lib/python3.12/site-packages/torch/_subclasses/functional_tensor.py:295: UserWarning: Failed to initialize NumPy: No module named 'numpy' (Triggered internally at ../torch/csrc/utils/tensor_numpy.cpp:84.)
  _conversion_method_template(device=torch.device("cpu"))
Traceback (most recent call last):
  File "/src/paired.py", line 14, in <module>
    assert torch.equal(xc64[:16],xc16) and bytes(xc64[:16].contiguous().view(torch.uint8).tolist())==bytes(xc16.contiguous().view(torch.uint8).tolist()),"STOP_SUPPORT_PREFIX"
                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'list' object cannot be interpreted as an integer
```

Independent raw-only auditor stdout:

```json
{"disposition": "STOP_NO_RAW_OUTPUT", "entries": [], "optimizer_updates": 0, "seed_reusable": false}
```

## Independent check

A separate networkless, read-only Docker auditor mounted `/out` read-only and verified it was empty, returning `STOP_NO_RAW_OUTPUT`, zero optimizer updates, seed not reusable. This confirms absence of partial results; it does not adjudicate the model hypothesis.

## Provenance and scope

The source's upstream runner is the byte-verified public-main runner, Git blob `ecd3a0414178f38535406573314793a40b353878`. The experimental wrapper, preregistration and initial freeze were uploaded to the dedicated branch and read back before the run; GitHub MCP adds a terminal CRLF to uploaded text, while normalized content matches local bytes. main advanced from frozen `f02ff323` to `a6329d5b` via unrelated #4832 extent-readout STOP evidence in `research/analysis/`; no path overlap.

This record makes no claim for or against support64, realtime adaptation, skill transfer, GUI task performance, concurrency, product readiness or execution authority.

