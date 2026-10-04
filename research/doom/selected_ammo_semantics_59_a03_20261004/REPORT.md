# Current-main HUD reader qualification for selected weapon ammunition — #59 A03

## Result

`PASS_HASHED_WAD_GLYPH_READER_AND_SAME_TIC_API_SCOPED`. The exact current-main V3 WAD-glyph reader returned health 100 and ammo 50 on both retained 640×480 frames. The underlying direct ViZDoom variables matched the same `GameState.game_variables` vector, and the episode tic stayed fixed across state capture and direct reads (tic 1 at startup; tic 36 after a neutral 35-tic coast). At both samples `SELECTED_WEAPON=2`, `SELECTED_WEAPON_AMMO=50`, and fixed slot `AMMO1=0`; all ten ammo slots are retained in `out/raw.json`. The visible HUD digits agree with the V3 reader and selected-ammo API. `AMMO2` and `AMMO4` both contain 50, so this run still does not identify a unique selected-weapon-to-slot mapping.

The second frame shows a nearby enemy while health remains 100. This records a changed scene during the input-free coast; it does not establish damage exposure, useful feedback onset, or recovery.

## Protocol and provenance

H/T/D/C/U is in `out/FREEZE.json`. One fresh Doom2 scenario config was explicitly pointed at the image's `freedoom2.wad`; the episode received no game buttons. The candidate and independent audit each ran once. The frozen reader source is current `main` `fdbe5182c57102916833f489cd07c60927e3de28`; exact Git blob IDs and byte hashes for V1/V2/V3 are in `source/GIT_BLOBS.json`. The WAD hash (`a8772e...ecd4b`) equals the reader's frozen expected WAD identity.

Image: `post-guard-game-59-4d74:20261004`, ID `sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378`.

Candidate command: `wslc run --rm --network none --user 65534:65534 --cpus 1 --memory 512m --workdir /out -v <A03>/source:/study/source:ro -v <A03>/out:/out:rw -e PYTHONPATH=/study/source -e PYTHONDONTWRITEBYTECODE=1 -e HOME=/tmp post-guard-game-59-4d74:20261004 python3 -B /study/source/probe.py`. Candidate exit 0; independent raw-only audit exit 0. WSLc warned the kernel lacks swap-limit capabilities / cgroup mount, so requested memory enforcement is unverified.

The freeze JSON's declared `created_utc` is 12:54:03 UTC, but its filesystem creation time is 12:55:03 UTC; the prelaunch receipt is 12:55:31 UTC and the container log begins at 12:55:34 UTC. Preserve the discrepancy: the exact freeze file predates execution, but its declared timestamp is not reliable.

## Scope limits

This qualifies the source-pinned pixel reader against a same-tic in-memory ViZDoom frame and engine values. Focus and surface metadata are synthetic labels for in-memory frames, not a live X11 pointer/window identity. No value was sent to the controller or model. This does not measure per-key admission/up/release, feedback during model latency, independent useful progress, damage response, bounded recovery, or MAP01 completion. It only resolves that `AMMO1` must not substitute for the selected-ammo signal in this sampled state.
