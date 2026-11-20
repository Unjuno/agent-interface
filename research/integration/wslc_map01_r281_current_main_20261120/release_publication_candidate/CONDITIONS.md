# Expiry release publication candidate

- Frozen source base: `381a21ace42891c2cd1e9cff3e231bec763ec2ba`.
- Candidate source delta: add `expired` to `ExecutorV12._publish_release_cause`'s accepted owner-release reasons; add one expiry publication regression to `cancel_release_publication_59`.
- Test backend: in-process Fake X and fake input owner. The fixture waits for the owner's independently recorded `expired` release before allowing executor cleanup, so this specifically tests publication of a verified expiry receipt before terminal publication.
- No native X server, GUI, WSLc, Docker, provider, or model was used.
- The regression expects one `input_released` event, before the terminal event, with the same verified neutral owner receipt and no input-authority grant.
- The isolated red run uses the unmodified base source. Its failure demonstrates that the base emits zero `input_released` events even though the terminal carries an expired interruption receipt.
- The test does not validate expiry scheduling races, native input release, task success, recovery reliability, or efficiency.

Earlier failed harness attempts and the pre-fixture Python 3.13 scheduling race are retained in separate `*-failure-*` and `harness-shape-error-*` logs and are not counted as passing evidence.
