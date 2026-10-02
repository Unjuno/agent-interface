# Retained CUDA finite-difference construction STOP (#4847 / #4849)

## Status and archival scope

**Retained result: `STOP_FINITE_DIFFERENCE_PROBE_IMPLEMENTATION`.**
This is archival preservation of the consumed allocation
`tiny-visual-extent-readout-4817-cuda-20260927-02`, not a new experiment
or a repair of its frozen sources.

The nine original files are preserved byte-for-byte from
[PR #4849](https://github.com/Unjuno/agent-interface/pull/4849), final head
[`d8cc8992b82fd1b4bd74b3f7207507179648ba90`](https://github.com/Unjuno/agent-interface/commit/d8cc8992b82fd1b4bd74b3f7207507179648ba90).
This report supplies qualifications without rewriting the original
[STOP receipt](STOP.md), [freeze](FREEZE.json), source, or logs.

## H / T / D / C / U

**H.** The historical construction question was whether the fixed-seed
extent-readout setup could execute deterministically on the pinned CUDA
environment. This allocation did not decide the pooling hypothesis.

**T.** The retained [stderr](runner.stderr.log) records a failure in
[`finite_difference_probe()`](run_cuda.py) at its first in-place
perturbation of a view of a grad-tracked leaf parameter. The
[exit receipt](runner.exit) is 1 and [stdout](runner.stdout.log) is empty.
Static source order places this failure before the call that generates
the train, base, and held-out datasets, before optimizer updates, and
before either construction fit or any formal fit.

The probe had already created diagnostic tensors and a diagnostic
`Model`, computed a forward pass and loss, and requested gradients with
`torch.autograd.grad`. Thus “before dataset generation / fitting” does
not mean that no model, tensor allocation, forward computation, or
autograd computation occurred. The planned 49-parameter finite-difference
diagnostic did not complete.

**D.** Preserve the original STOP. The value
`construction_fits: 2` in [FREEZE.json](FREEZE.json) describes the planned
two-arm allocation, not completed work. The retained
[STOP_AUDIT.json](STOP_AUDIT.json) records zero optimizer updates, zero
construction fits, and zero formal fits; no `RAW.json` is present in the
nine-file original bundle.

The label `PASS_STOP_EVIDENCE_INTEGRITY` in that audit is a historical
receipt. This archival review does not rerun the historical check or
promote the label to an experimental PASS, a completed construction
result, or evidence that the scientific hypothesis passed.

**C.** The frozen [CUDA runner](run_cuda.py) and [CPU auditor](audit_cpu.py)
remain unchanged. Archival verification is limited to static source and
receipt reading, JSON/text checks, exact Git blob identities, retained
receipt hashes, and link/index checks. No historical code, experiment,
test, or auditor was executed, and no retry or repair of the consumed
allocation is part of this preservation.

**U.** The original receipt references a full GPU XML snapshot retained
only on the originating PC. That XML is not among the committed nine
files, was not provided for this archival review, and has not been
independently verified here. The retained [image identity](image.txt) is
not a substitute for the missing XML or fresh GPU attestation. There is
no training-quality, efficacy, GPU-benefit, formal-fit, or adoption claim.

## Distinct successor

[PR #4851](https://github.com/Unjuno/agent-interface/pull/4851) retained the
separate #4850 allocation under
[`tiny_visual_extent_readout_4817_cuda_v3/`](../tiny_visual_extent_readout_4817_cuda_v3/).
It is a distinct successor, not a replacement for this original STOP.
Its execution and audit results do not retroactively complete this
allocation or alter its immutable evidence.

## Exact original blob manifest

All entries retain mode `100644` and their original Git blob SHA:

| File | Git blob SHA |
|---|---|
| [FREEZE.json](FREEZE.json) | `74e07a230fa37a8198ad8221f33b2ae7b6494408` |
| [STOP.md](STOP.md) | `b54fe9172c874aa97f8f9136a7c8c97653ac03f3` |
| [STOP_AUDIT.json](STOP_AUDIT.json) | `1e96f1030cb5a2981ccc47ecd5450681a8b8c83d` |
| [audit_cpu.py](audit_cpu.py) | `765085f1701d6c90f4d77ed595747f56e138d66e` |
| [image.txt](image.txt) | `243afb9f03dd818d215c12c5086acd69a3ee28b6` |
| [run_cuda.py](run_cuda.py) | `bd6a3d16f643b822a3d7b9d8daeac70d0ed239d3` |
| [runner.exit](runner.exit) | `f33dfa25aa16a97ca941fe1d9cabdc3689179f3f` |
| [runner.stderr.log](runner.stderr.log) | `662face15ed00f88798c7045cf5db2acaf26deb5` |
| [runner.stdout.log](runner.stdout.log) | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` |
