# #1888 MAP01 loaded-fixture timeout precondition

Decision: **PASS_MAP01_FIXTURE_TIMEOUT_PRECONDITION_SCOPED**.

## Result

The retained `map01-threat-contact-v2` save is at episode tic **1366**. A loaded ViZDoom1.3.0 episode is immediately terminal from the episode-timeout gate exactly when:

`episode_timeout_tics < fixture_episode_tic`.

Equality is nonterminal.

Formal first outcome, six fresh load/read-only DoomGame instances:

| case | timeout tics | loaded tic | episode_finished |
|---|---:|---:|---:|
| ticks-1365 | 1365 | 1366 | true |
| ticks-1366 | 1366 | 1366 | false |
| ticks-1367 | 1367 | 1366 | false |
| ticks-1400 | 1400 | 1366 | false |
| seconds-39 | 1365 | 1366 | true |
| seconds-40 | 1400 | 1366 | false |

Candidate/expected mismatch0/6; player-dead/kill/death counters remained clean6/6. Frozen formal source contains no `advance_action`, `make_action`, `set_action`, or `send_game_command` call. Task-input actions0.

## Preformal correction retained

The Issue initially predicted terminal at `timeout_tics <= fixture_tic`. Excluded construction directly falsified equality: timeout1366 at loaded tic1366 was nonterminal. Formal was still0, so the H/D predicate was corrected and explicitly recorded before source freeze. No post-freeze threshold/gate change occurred.

The construction incident that motivated this study used 30 seconds: 30×35=1050 <1366. That necessarily made the scorer epoch terminal immediately and explained the observed zero-effect clock. Restoring the retained60-second envelope on a fresh excluded construction produced a nonterminal initial scorer sample and one independent `KILL_COUNT_INCREASE`; neither construction run is pooled into this formal.

## Environment / integrity

Immutable runtime artifact:
- workflow run34973453255 / artifact10398313098;
- artifact ZIP SHA-256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`;
- runtime source base `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`;
- artifact manifest verified source files2592 / wheels12 / hash errors0;
- ViZDoom1.3.0;
- exact save SHA-256 `cc5302aa9cda3960248733caa96da1b53adcc4b6a1a2dcfb80675650c9350401`;
- exact Freedoom2 IWAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.

Source was published/read back before formal: 7/7 Git blobs exact. Formal invocation1/reruns0/replacements0/tuning0. Independent audit PASS/errors[]. Copied-result corruption controls6/6 reject.

RESULT SHA-256 `54d7cbc8d4b46333b140af418728b0705d492563dd4370cc2bf9524d49808df5`.
AUDIT SHA-256 `d58283f448bc28f3fffe088d49a944d60c217c6ceb1837ae6fe8e85a9f47fe6b`.
CORRUPTION SHA-256 `e14cd52edef8fc0facfd452ee5b1f867c0490c0f71a477aeb993f716b9ed84cd`.

## Interpretation

A live MAP01 task-effect/scorer allocation must validate the loaded fixture tic against the configured episode timeout **before** starting the append-only scorer epoch. For this fixture,39 seconds is invalid and40 seconds is the smallest integer-second timeout that clears the episode-time boundary. A larger task horizon may still be chosen for other reasons; this result does not prescribe60 seconds globally.

This result does not establish a TASK_EFFECT event, physical actuation lineage, useful occupied control, or recovery efficacy. The remaining live instrumentation gap is to connect the already-proven InputOwner-v12 physical edge lineage to the MAP01 plan/actuation IDs while preserving this timeout precondition and the independent scorer.
