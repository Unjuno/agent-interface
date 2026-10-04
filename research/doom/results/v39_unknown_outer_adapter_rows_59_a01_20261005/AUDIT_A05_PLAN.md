# Independent raw audit — A05

## H / T / D / C / U

- **H:** The retained A01 red and green results correctly demonstrate that unknown outer adapter rows invalidate the affected V39 edge receipt, while the unique known pair remains intact.
- **T:** Independently verify immutable A01 run outputs, source/test/fixture/runner hashes, original candidate pre/post inventories, retained STOP evidence, and three mutation controls. This is a new audit protocol version after A02–A04 auditor STOPs; neither regression test is rerun.
- **D:** One WSLc invocation must exit 0 and emit `PASS_SCOPED_RAW_AUDIT`, verify all frozen inputs and 15 checks, and reject all three deliberate report mutations. Any failure remains the terminal audit outcome.
- **C:** Raw audit evidence catches provenance mismatches and report mutations but cannot establish live GUI or application effect.
- **U:** Saved synthetic projector results only. No live X-server key release, physical dwell, application consumption, useful task effect, recovery benefit, or MAP01 completion is established.

## Frozen execution bound

One WSLc invocation only, image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, `--pull never --network none --cpus 1 --memory 512M`; source and evidence read-only, dedicated audit mount. No regression rerun, retry, model, game, GUI, GPU, input, network, or package installation. The cgroup/swap warning is retained; configured memory is not called swap-bounded.
