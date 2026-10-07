# A03 result

- Outcome: `PASS_METHOD_SCOPED` after one successful image build, one container start, and one saved-raw audit.
- All 11 focused fake-X batch-composition tests passed under pinned Python 3.12 and the frozen package set.
- The raw event and independent audit confirm keycode 38 was observed down after injected `sync()` acknowledgement loss, the emitted measurement was `KEYMAP_EDGE_UNCONFIRMED` with null bracket and actuation ID, and cleanup verified key-up with an empty final key state.
- All source/harness hashes, image identity, readonly source mounts, no-network policy, and 1 CPU / 1 GiB / 64-pid caps passed audit.
- Scope is limited to Python/Linux dependency and fake-X regression reproducibility. This does not establish real X11 behavior, GUI/application consumption, physical keyboard state, threat response, Doom progress, or live #59 gate completion.

## Identities

- Candidate source commit: `ca8f4113510b4b01a8e7d001dfe812dcc7b640a9`
- Freeze commit: `bc5c1016ef313da13a7acb3a8de9ccd1b6fa5d40`
- Container image ID: `sha256:b82a3260f3e5839b9dce6d745233f09c9189d5f2154cf7a6d18e24d190c10907`
- Container ID: `5dbe4baddd2e67dfac421337e6b9ca15c0764f736a62a0f004f72a9dd3c869c9`
- Container exit code: `0`
- Tests run: `11`
- Audit status: `PASS_METHOD_SCOPED`
- Raw SHA-256: `9ad89f17044f2bad6a4247b791903e6d7fb6dfc773703c6f1933bf18e6855694`
- Event SHA-256: `73522cff8ae5e11591f42cd45af7ee17d8230478b2a2a7e8fd740e50b15d7bfc`

## Retained artifact hashes

- `BUILD.log` SHA-256 `fdac73a41e29393055dbfc8e2226d6405c95264888f64b6c52970d6aad5ed706`
- `RUN_STATUS.txt` SHA-256 `774c1b877759995e5f1275585bc5c22c167cee54bc5fe0856e50793256e292bc`
- `TEST_RAW.json` SHA-256 `9ad89f17044f2bad6a4247b791903e6d7fb6dfc773703c6f1933bf18e6855694`
- `TEST_EVENTS.jsonl` SHA-256 `73522cff8ae5e11591f42cd45af7ee17d8230478b2a2a7e8fd740e50b15d7bfc`
- `AUDIT.json` SHA-256 `06de7863f1f4609cd11015d7cbdf4609a82a100339fb643738b9042a5b7dd79c`
- `CONTAINER_STDOUT.log` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `CONTAINER_STDERR.log` SHA-256 `d1e24d502614ad283376d4e132c3427a67762a2649ddd96121f3b48600c0f1e9`
- `IMAGE_MANIFEST.json` SHA-256 `43cb6725fa987556458ab0a1295547f3f7fc2a4b86736823b9d6d6e09d35c538`
- `CONTAINER_INSPECT_BEFORE.json` SHA-256 `85c93f3702f141ec9a24e2a70c7ab6daf49e66b3c2adb9576374dd2fc429df4f`
- `CONTAINER_INSPECT_AFTER.json` SHA-256 `028048c79b7deb0a78315865f559399b1d74404fec864984f196558c82321063`
