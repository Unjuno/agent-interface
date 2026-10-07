# A02 result

- Outcome: `FAIL_TESTS`; the image built and the bounded container ran once.
- All 11 focused tests errored during import. A01’s `research` namespace lookup was fixed; the next missing dependency was top-level `real_app_suite_v1`, imported by `research/observation_gating/gui_suite.py` from `research/real_apps_v1/`.
- The saved-raw auditor ran once and produced `FAIL_AUDIT`. Source and harness hashes, Python/dependency versions, cgroup caps, image identity, and existing readonly mount policy passed. Test-success and behavior-event predicates failed because no test setup completed and the JSONL event file was empty.
- No retry or second run was made. The container was removed by the frozen script.
- This is a harness dependency-closure failure, not regression behavior evidence and not live #59 evidence.

## Retained artifact hashes

- `BUILD.log` SHA-256 `7e3991cb8c29cb7034837dfcc1d9cfdcce98db5209a9c61d15e95b1361267841`
- `RUN_STATUS.txt` SHA-256 `141f07d40fab6824e254d0c97905f763a034dc48a11b0247d7525b67589a99ad`
- `TEST_RAW.json` SHA-256 `e10fab96d4f5e0e25601098635f05d8587b00e46b65fd501764ceadce2171865`
- `TEST_EVENTS.jsonl` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `AUDIT.json` SHA-256 `a7284eacd08b60f6360d2f9091387c6ec24e707775b2c8b462b11e8cee6edd86`
- `CONTAINER_STDOUT.log` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `CONTAINER_STDERR.log` SHA-256 `ea61c376e3038e326f98760ffd1047fd5d62c6520adc2d356a8c860110e6f99f`
- `IMAGE_MANIFEST.json` SHA-256 `9d719fcd4a9ac6ae5756c5757e14a9e9bac92bcf5b9299578ce9dbbf72027eb1`

- Image ID: `sha256:1fa60ebae24271ba3f74eb75deb073d7802d395c457cd322a9ef1ee909880cd5`
- Container ID: `ecc32507bf0c8eeca4f3239a0f2a4ef95f8f942a089e907cec8077c421f4ece6`
- Auditor status: `FAIL_AUDIT`
