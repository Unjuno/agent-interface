# Packed historical-snapshot prefix index — #4355

Preformal publication, allocation `packed-prefix-p9s4-20260925-01`.
Base main `4a1f3957e91b412a64769199f78f2c4b0102d28b`.

This evidence-only successor to closed #4122 changes the representation of the full eager prefix index. It does not change the existing parser, page size, live capture or authority. #4161's RSS study and #4068's demand-built indexing remain separate.

`packed.py` is the exact candidate. `PROOF.md` gives the conditional equivalence proof, variable table and unit check. `preformal/` losslessly retains the complete 18-member source/plan/proof/corpus/schedule/environment/freeze bundle BEFORE any formal worker. No source is regenerated from prose. The literal fixture bytes are hash-bound in the corpus/freeze and are retained locally for the result bundle; their deterministic generator is included. This source capsule is not a claim that measurements have run.

H: fixed-width immutable 40-byte prefix entries preserve every historical query and can reduce retained allocation without excessive query/preparation time.
T: 30 resource workers (three fixed-1MiB densities, two representations, five repetitions) plus two contract workers; separate uninstrumented timing and declared memory preparation passes. Every formal batch is single-use.
D: full semantic/source/process evidence plus12 effective mutations; separately candidate/eager retained median ratio<=0.35 at8192 lines and wall ratio<=1.50 at each density. Failed cost gates remain HOLD.
C/U: full count pass, binary search, transient digest decoding and copy costs are charged; retained traced memory is not RSS. Fixed trusted snapshots, one environment, technical repeats, no live model/GUI/task/input, no production/default promotion.

## Read the frozen source

From this directory:

```sh
python -S -B restore.py preformal /tmp/packed4355-source-review
```

The restorer is data-only. Do not invoke consumed formal launchers during review. The complete formal result and a separate read-only verification command will be added after the first outcome. The owned branch must not be merged on construction evidence alone.

## Construction retained locally

Six test methods pass, including exact inherited-method checks, full prefix-table comparisons, 480 small contract outcomes and ten effective row mutations. First fixture generation failed because a helper parameter collided with a deliberate Boolean-offset test; its original source/error and subsequent excluded correction are retained. Formal workers at publication:0. Same-author independent implementation is not an independent human review.
