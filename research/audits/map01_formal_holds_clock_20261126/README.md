# MAP01 held-input cancellation attempts and post-load clock diagnostic

On 2026-11-26 JST, three separately allocated WSL2/X11 trials each ended in HOLD. The related clock diagnostic passed its own narrower gate. No provider or model calls occurred. The game trials were collected at source commit `7f93191a2b7c6c96d6436a8776574da71b4c91d5`. [Machine-readable summary](SUMMARY.json)

## Registered conditions

The three trials used seed `26011261`, MAP01 skill 1, the same `map01-threat-contact-v2` saved fixture, and ViZDoom 1.3.0 at 35 tics/s in asynchronous spectator mode. The same engine, game-data and save digests are recorded in the summary. Each allocation permitted one run, at most one 4.5-second Shift modifier hold, and no retry. The target ran on a private authenticated X11 display under a dedicated systemd control group with private network and temporary namespaces, a 60-second runtime limit, and a five-second stop timeout. The independent V15 scorer stayed outside the controller's screen policy.

The registered cancellation trigger required a fresh image of the same target showing lower health while independent X11 readback showed the modifier held. A qualifying run required one observed trigger, one cancel, a cancelled terminal during the hold, verified key-up and neutral readback, and complete owner and display retirement.

## Formal outcomes

| Trial condition | Outcome | Evidence |
| --- | --- | --- |
| 30-second engine ceiling | HOLD | The save loaded at tic 1366 against a 1050-tic ceiling. All 167 independent samples showed finished, alive and no exit. The first sample preceded input. One hold completed normally and no cancellation was sent. |
| 75-second ceiling with getter-only readiness | HOLD_PREINPUT | Post-load getter samples 100.123 ms apart both reported tic 1366, active and alive. The readiness gate stopped dispatch. Zero programs were accepted and zero inputs or cancels were admitted. |
| 75-second ceiling with neutral equal-refresh readiness | HOLD_NO_OBSERVED_TRIGGER | The gate passed with immediate and waited deltas of 1 and 71 tics. One hold completed normally. All 40 independently checked HUD observations showed health 97, with zero damage triggers and zero cancels. All 165 independent samples showed active, alive and no exit. |

The first trial's raw V12 score reports `map_exit=true`. That result came from the short control-wall interval, about 4.715 seconds, despite the saved episode already exceeding the engine limit. The independently adjudicated result is **no verified map exit**. All 167 independent scorer samples recorded `map_exit=false`. The source correction merged at `7ec12eef766f212e0754b3818e43a3d60feeeb14`. It checks engine timeout, distinguishes the native result from a fallback tic-limit inference, and records the actual count of final scorer refreshes. The original score remains in local custody for reproduction. [V12 scorer](../../doom/session_map01_v12.py) · [V15 independent scorer](../../doom/session_map01_v15.py) · [Offline regressions](../../doom/test_session_map01_v12_final_score.py)

The getter-only gate in the second trial used no refresh. Its earlier pre-load clock probe used refreshes on both sides of a wall interval, so the two readings characterize different observation methods. In the third trial, the pre-load clock probe used two refreshes. After the fixture loaded, the readiness gate used four one-tic refreshes before the controller's first screen observation. Each had a zero previous action vector and neutral X11 readback. The readiness gate required an active, alive episode, at least 525 tics remaining, at least 35 extra tics in the waited pair versus the immediate pair, and at least 35 tics remaining after subtracting both requested tics from the waited delta. It also required a waited pace of 25–45 tics/s and a gate no more than two seconds old at submit. The measured hold used zero refresh calls. Both admitted holds ended with verified key-up and neutral X11 readback. Each formal trial verified retirement of its owned scope.

## Separate post-load clock diagnostic

The clock diagnostic returned `PASS_SCOPED`. It restored the same save into three fresh game instances in fixed order. It dispatched zero task input and made zero model calls. The getter-only case requested no refresh. Both refresh cases requested two one-tic updates each. The waited pair inserted a two-second passive interval.

| Case | Endpoint tics | Delta | Wall interval between endpoint getters |
| --- | --- | ---: | ---: |
| Getter only | 1366 → 1366 | 0 | 2.000346 s |
| Immediate refresh pair | 1372 → 1373 | 1 | 0.028454 s |
| Waited refresh pair | 1372 → 1443 | 71 | 2.029145 s |

All three cases remained active and alive. The waited pair advanced 70 tics more than the equal-refresh immediate control. Deducting both explicitly requested tics from the waited delta leaves 69. This supports the scoped clock comparison on this fixture. ViZDoom refresh processes a requested tic, repeats the previous action and updates state and reward. The result captures different readouts across equal refresh counts. The individual tics' timing independent of the observer remains unresolved.

The three formal outcomes preserve the distinction between engine timeout, a pre-input veto and absence of a valid trigger during an admitted hold. They provide sampled readiness and ordinary input-release evidence. Triggered cancellation, MAP01 completion and general reliability still require their own evidence.

## Evidence commitments

These SHA-256 values bind the separate preregistrations and the file manifests of the locally sealed original records. All 9,551 listed entries were checked against their manifest digests. Two setup stops are listed separately. The diagnostic display gate stopped before a game launch (`HOLD_BEFORE_GAME`). A separate formal launcher stopped before importing its runtime (`HOLD_BEFORE_IMPORT`). Both had zero game starts, task inputs and provider calls. Public readers can inspect the method and aggregates. Rechecking the private logs, saved frames and process custody requires authorized access to the sealed local originals.

| Record | Files | Registration SHA-256 | Manifest SHA-256 |
| --- | ---: | --- | --- |
| 30-second engine ceiling | 2,395 | `919741c2c566923681c1ad79a79f0b1244e2c2f902f31127fb7e546822d069a6` | `00ff9918e418471c2818b9b8e947583ff808d40551c219793832119a645c974d` |
| Getter-only readiness | 2,326 | `1062931a6f1e4b862c1974cb77fcc60ec70ba712644163d3c72c56b49d060b1c` | `440d7afd76a64013a7a890fad8bf9b3fd70084e62d68615212e8898a6d5a5e5a` |
| Neutral equal-refresh readiness | 2,412 | `134d041dcf58571f0512c481557a1c4ee400de994fafe5cf6abdc03996b344b9` | `f5e75b647ceb08e5976a8637c1c2fdad7833da50c23be31fb77750b8de5d2ac1` |
| Clock diagnostic | 106 | `c2cd284a5e6590c721e0b8b1e7eff1ef7fb163cfd8f82e82f7db8debf8c36b47` | `d1cd1269c527f83a38ad74e64707c39848a00ac1780a79f7d02311ce4684d7de` |
| Display setup stop | 14 | `e32d2c51f6908b1568c8310bca313fadf50059e8dbfccd9c7a0a0f7f01371ce5` | `6507869f68024b9010a2220a613d801bb487cf31d17680ba2f7ad71205067958` |
| Launcher import setup stop | 2,298 | `1aca402ed1238717a2c668f9e734d527b91b52080ae95901e2dcdb6ffa251a67` | `84257b2a25e3df0ba445c8b639e138a5b30e7dbd3bd56d9fc84e22bd5f5d0166` |
