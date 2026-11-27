# Camera block-motion screen R02

**Disposition: `FAIL_SCOPED`.** The fixed local block-matching method does not meet the preregistered signal criterion on the retained episode.

| Measure | Result |
|---|---:|
| Adjacent pairs / typed health-loss pairs | 52 / 4 |
| Raw world-crop RGB MAE AUC | 0.417 |
| Prior global-translation AUC (recomputed anchor) | 0.406 |
| Fixed blockwise-compensated AUC | 0.427 |
| Blockwise AUC gain over raw | 0.010 |
| Loss pairs above blockwise no-loss median | 1/4 |
| Frozen pass criterion | Not met |

Normal and `-O` candidate outputs match. The independent audit passed in both modes and recomputed all 52 pairs and 1,664 local tile offsets. Blockwise matching improves this episode's AUC slightly over both comparators, but falls far short of the required +0.10 gain and does not separate the health-loss pairs. Reject this fixed blockwise feature for this screen; do not promote it to a detector.

R02 reuses the same one-episode V39 dataset and four positive labels as A01, so it is not independent confirmation. Local matching can align away meaningful object motion or match unrelated repeated textures. No semantic threat labels, live game, input/release, task effect, gameplay benefit, or reliability were measured. The broader #59 live-control gate remains open and still lacks the isolated target/assets.

See the [frozen method](FREEZE.json), [conditions](CONDITIONS.md), [independent audit](AUDIT.json), [raw outputs](raw/), and prior [global-translation screen A01](../camera_compensated_motion_a01_20261008/README.md).
