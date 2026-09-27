# Retained result — O2 contiguous tile materialization

## Chronology

The allocation ran locally before Issue #4092 existed because the earlier GitHub connection exposed no write actions. The original local freeze and executed bytes are preserved exactly. Issue #4092 is retrospective publication, not preregistration.

Parent #4065 remains `HOLD_ATTRIBUTION_NOT_ESTABLISHED`: its compression-majority gate passed but its comparison-expression <=0.15 gate missed. The earlier vectorization allocation remains its own timing/cleanup HOLD. Neither predecessor is rewritten.

## H / T / D / C / U

**H.** Contiguous materialization before tile byte serialization should reduce the dense serialization path: each of the three dense conditions candidate/vector median ratio <=0.85, median-of-three <=0.80, and each of nine other changed conditions <=1.10, with exact wire/pixel equivalence.

**T.** Supplied Linux x86_64 execution container; guest-reported AMD EPYC 9V74; CPython 3.13.5; NumPy 2.3.5; zlib 1.3.1; CPU affinity [1]; no frequency lock or Docker/OrbStack image identity. Fifteen retained RGB before/after pairs at 640x480, 1280x720, 1919x1079; unchanged/local/corners/row/dense; tile edge 64; zlib level 1. Legacy/vector/contiguous arms; three warmup triples plus 21 timed triples per condition; 315 timed triples / 945 update encodes; three immutable five-condition batches; no formal retry.

**D.** `PASS_CONTIGUOUS_TILE_COPY_SCOPED`. All 15 conditions, 315 measured triples, 45 warmup triples, and three external exit-0 receipts reconcile. Exact packet bytes/pixels, frozen identities and eight semantic corruption controls pass. Dense paired median ratios: 0.4670, 0.4803974972, 0.5084204259; median-of-medians 0.4803974972. All nine non-dense changed conditions meet <=1.10.

Representative dense wall medians (contiguous/vector): 3.230/6.753 ms; 9.611/20.242 ms; 22.795/45.094 ms. These are technical repetitions, not independent task samples.

**C.** `np.ascontiguousarray` can allocate/copy before `tobytes`; it can regress small/already-contiguous tiles or under memory pressure. The full-frame alternative is still compressed before packet selection. CPU/cache/allocator/NumPy details are plausible mechanisms, not semantic guarantees.

**U.** Development-known corpus, one environment, no held-out GUI/domain, end-to-end latency, model/token/task benefit, measured peak RSS, cross-platform or production claim. Same-author separate auditor is not external review.

## Publication verification

The retained allocation is reconstructed from four content-addressed patch parts. Local concatenation yields 1,327,767 patch bytes, SHA-256 `513ca7552d4240474020c337f53bfdf846751d9f4c5ed65dc7c11fbbe3b4b5ca`. Applying it to an empty git repository restores 131 files / 1,876,594 bytes. Re-running `audit.py --controls` exits 0 and produces bytes exactly equal to retained AUDIT.json; both SHA-256 `efe9beed96288ebd32f5e4cc0d5ff0e59a322fe07d48903757edf155c9686ec5`.

## Integration decision

Retain as a candidate for a separately frozen held-out/current-path transfer only. Do not change `research/observation_tiles/tile_transport.py` or any runtime default from this result alone.
