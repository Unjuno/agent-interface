# Mindustry offline asset materializer v1

H: exact already-mounted Mindustry JAR/save bytes can be staged without network through fail-closed identity checks and atomic directory publication, so partial/mismatched assets never appear as `ASSETS_READY`.

T: tiny deterministic fixture bytes exercise the same mechanics and filenames; production hashes remain metadata only. Sources must be regular non-symlink files. Output must not exist. Both copies are fsynced and verified in a sibling staging directory, manifest is fsynced, then the directory is atomically renamed and parent fsynced.

D: PASS only if one correct staging publishes exact bytes+manifest and all wrong-jar, wrong-save-after-first-copy, source-symlink, and preexisting-output controls fail with no new final publication. One formal invocation, zero reruns, independent audit and corruption controls.

C/U: mechanics only; no real JAR/save materialized, no game/GUI/model call, no live lease or provider-economics claim.
