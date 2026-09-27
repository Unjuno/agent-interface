# Preregistration — Issue #3869

Allocation: `needle-intent-distill-3458-pilot-06-isolated-shift-audit`. Successor to #3847; the predecessor's failed result and its review findings remain unchanged.

## H / T / D / C / U

**H — hypothesis.** The fixed pilot-04 hybrid Needle maintains useful authority-neutral proposals when only CORRECT covariates move toward the decision surface. CONTINUE and WATCH controls stay byte-for-byte generated from the original balanced generator. The independent auditor can reconstruct each model prediction, teacher label, control input, yield reason and summary from retained raw evidence.

**T — treatment.** Three fresh deterministic seeds 3467–3469. Train the unchanged 6→16→16→3 tanh model on 2,048 rows/class, AdamW lr .008, 700 steps, batch 64, CPU one thread. Evaluate 1,024/class/seed on (a) IID balanced controls and (b) isolated shift: CORRECT has signed |dx| in [.071,.149], |dy|≤.10, |vx|,|vy|≤.05, confidence [.80,1], visible=1; CONTINUE and WATCH exactly reuse the unmodified `balanced_class` generators and seed mapping. Include 1,536 deterministic boundary rows, 2,000 single-row latency probes, and five explicit invalid metadata/scope/epoch/envelope/non-finite cases per seed. Persist all suite rows, state weights, latency samples and invalid inputs. NaN is encoded as the literal JSON string `"NaN"` and independently reconstructed as IEEE NaN by the auditor.

**D — decision.** Every seed must meet shifted accepted accuracy ≥.95; each class accepted coverage and accepted recall ≥.75 and ≥.95 respectively; false CORRECT ≤.5%; 1,536/1,536 boundary YIELD; all five invalid inputs independently recompute to the expected YIELD; and CPU p95 <60ms. IID is diagnostic and cannot rescue the shift suite. Any gate miss is FAIL; any provenance, completeness, or audit error is STOP/HOLD, never PASS. Exactly one formal process; no retries, retuning, or seed replacement.

**C — constraints.** Cached `needle-pilot05:local` image only (image ID recorded in FREEZE); CPU-only, `--network none`, `--read-only`, 2 CPU / 4GiB, read-only source and dedicated writable output. No GPU allocation (parallel Issue #3851 is GPU-focused; this allocation does not reserve or use RTX 3080), downloads, cache pruning, external inference, GUI, real action, or execution authority. If Docker stops responding, stop immediately, preserve the exact STOP and do not rerun the formal allocation.

**U — limits.** Hand-authored synthetic teacher only; not Astra labels, perception, pixels, GUI/servo behavior, task effects, real-time end-to-end, general Needle quality, runtime integration, product readiness, or authority evidence. Three seeds characterize only this declared isolated shift.

## Formal allocation

One container process trains all three fixed seeds and writes exactly one `FORMAL_RESULT.json` into a new empty `formal/formal-01` directory. Frozen source and auditor hashes, branch, base SHA, image ID, device and Docker constraints are captured in `FREEZE.json` before invocation. No formal run begins unless local Docker construction tests pass and this preformal commit is pushed and recorded on Issue #3869.
