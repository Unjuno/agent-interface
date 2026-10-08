# Checkpoint delivery representation archive rescue

Source PR #6918, remote `research/6089-delivery-01a0ff59`, exact tip
`5e02b30977dc8412c715aa22dab718630906f4ad`. Preserve all 45 package files,
including original raw, receipts, source witnesses and provenance qualifications.
Current analytical navigation is regenerated separately, not copied from old main.

The archival tests verify 44 manifested files plus the manifest against original
Git bytes, six inert source witnesses against historical Git, and the complete
24-row raw-only audit and all eight copied-raw corruption outcomes normally and
under `-O`. They do not import the producer or retained candidate/auditor.

The historical counterexample remains: three empty decks were classified fresh
and accepted by the retained auditor. Explicit MISSING normalization removes those
three mismatches; nine nonempty case pairs are unchanged. This is a finite model
and archive comparator, not a deployed adapter, physical-safety or live result.
Historical construction-test UTC remains unknown. No formal allocation or recorded
matrix is regenerated; old seven nonempty fixtures and original result stay intact.

```sh
python3 -m unittest discover -s runtime/results/checkpoint_delivery_rescue_6918 -p 'test_*.py' -v
```
