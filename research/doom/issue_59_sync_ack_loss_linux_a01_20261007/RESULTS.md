# A01 result

- Outcome: `FAIL_TESTS` after one successful image build and one container start.
- The frozen runner reports 11 tests run, 0 assertions completed, 11 setup errors, all from `ModuleNotFoundError: No module named 'research'` while importing `research.observation_tiles.tile_transport`.
- The container had only the `research/live_control` and `research/doom` trees mounted, and the runner did not add `/workspace` to `sys.path`; the import could not resolve the repository namespace package.
- The one saved-raw audit was attempted once and crashed with `KeyError: 'down_after_cleanup'` because no evidence row existed. No `AUDIT.json` was produced.
- No retry or second run was made. The container was removed by the frozen script; a later Docker `ps` showed no active containers.
- This result is harness/import failure only. It says nothing about the regression behavior, real X11, physical input, GUI effects, or the live #59 gate.

The initial direct shell launch failed before the script ran because the committed file lacked its executable bit. The runner mode was corrected in a separate commit; no output or experiment state had been created by that launch failure.

## Retained artifact hashes

- `BUILD.log` SHA-256 `cc10f493c3413a5ae2f8268ca810af60e1a8724a322ea856e6efe9314e9774dc`
- `RUN_STATUS.txt` SHA-256 `141f07d40fab6824e254d0c97905f763a034dc48a11b0247d7525b67589a99ad`
- `TEST_RAW.json` SHA-256 `54984888c158ae920e039ffa80e834dbbef6a1e2dfed8aacdd000e0a48431f14`
- `TEST_EVENTS.jsonl` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `CONTAINER_STDOUT.log` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `CONTAINER_STDERR.log` SHA-256 `c2a75a5daf4b79dcc005fa2bf79546954aa9df9dc6d144fb2d524fa3a196b91c`
- `IMAGE_MANIFEST.json` SHA-256 `2dcb121c357714379d87a53d52078bc3c268ccd3eba418ee6ef3376bfe2f054a`
- `CONTAINER_INSPECT_BEFORE.json` SHA-256 `f71aab9b90e290022d87a051aa1a5c5bfe4f72c421c5942ae50784fc1c55f093`
- `CONTAINER_INSPECT_AFTER.json` SHA-256 `5a79750a3ed156bf16c65a669dfcf3a6f7e6ee585f936903f45be8c7a17f7ab0`

- Image ID: `sha256:d4ed375896dee3b0cdd37f099784d119a803a3aad2dd5416c038e147a686d406`
- Container ID: `9aa04503690f48a437be75f749d5117d6b1ce30cb46b747f32b2431e10d9742d`
- Events SHA-256 (empty JSONL): `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
