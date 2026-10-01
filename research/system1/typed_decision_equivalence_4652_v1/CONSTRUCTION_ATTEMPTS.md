# Excluded construction gate history

## Attempt 001 — STOP before GPU/model initialization

The first local Docker invocation of `source/construction.py` exited 1 immediately with `ImportError: cannot import name 'CacheHandle' from 'cache_mechanics'`. The local study package had copied the #4623 helper, while the new control correctly expected the generation/bundle/prefix-bound handle from #4639. No model was loaded, no CUDA tensor or question was evaluated, no construction control passed, and no formal row was produced. This is a harness-source mismatch, not an outcome for the hypothesis. The formal invocation count remains zero.

The original preregistration is preserved as `FREEZE_ATTEMPT_001.json` and in GitHub commit `5362c4dd7711adffcbc397ec8470b27685ab1f15`. A corrected source/freeze revision is appended on the same dedicated branch and recorded in the Issue before any further GPU construction work. Formal remains prohibited until the corrected construction gate passes; the one-formal-invocation limit is unchanged.
