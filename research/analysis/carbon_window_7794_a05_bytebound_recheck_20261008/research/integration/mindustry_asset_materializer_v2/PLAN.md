# Mindustry offline asset materializer v2

H: preserving caller-supplied source paths through lstat/O_NOFOLLOW (without Path.resolve) closes the v1 symlink identity bypass while leaving atomic staging semantics unchanged.

T: one semantic repair from retained v1 failure: use absolute path normalization without symlink resolution. Harness-only repair: correct Python lexical published-file order. Same tiny fixture bytes, same production metadata, same negative controls, source-first freeze, one formal invocation, zero reruns.

D: PASS only if good staging is exact and wrong-jar, wrong-save-after-first-copy, source-symlink and preexisting-output controls all fail closed with no unintended final publication/stage residue; independent audit and corruption controls agree.

C/U: mechanics only; no production binaries, GUI/game/model/live lease or provider-economics claim.
