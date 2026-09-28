# Native Windows junction parity successor for #4882

This is a distinct follow-up to allocation 01's preserved WinError 1314 STOP.
It does not retry that allocation or change its symlink fixture. Allocation 02
uses unprivileged NTFS directory junctions to exercise the same frozen #4876
candidate resolver on native Windows.

## H / T / D / C / U

**H.** The unchanged candidate resolver will return canonical in-root paths for
regular files and in-root directory junctions, while refusing an external
junction, traversal, an absolute host path, and a missing path.

**T.** The exact candidate copy, runner and independent auditor are pinned in
`FREEZE.json`. One CPython 3.12.10 / Windows 11 / NTFS runner invocation creates
a unique temporary repo and outside sibling, uses `mklink /J` only to construct
one in-root and one external fixture, then evaluates nine frozen cases. The
runner saves its raw result and leaves the fixture alive for a separate
read-only auditor invocation. The exact per-run commands and hashes are kept
under `results/allocation-02/`.

**D.** PASS requires exact canonical outputs for the root aliases, regular file
and in-root junction; rejection of external-junction, lexical/encoded
traversal, and absolute paths; fail-closed missing-path behavior; a separate
auditor pass over both raw rows and live junction targets; and verified fixture
cleanup. Setup failure is STOP, not a partial pass.

**C.** The `resolve_host_path` function is copied from the pinned #4876 blob;
the frozen comparison checks its function AST against that upstream source.
Only the Windows fixture primitive differs from allocation 01. No broker `serve()` or
host-model CLI is called; `mklink /J` is fixture setup, not a broker child.
There is no Docker/OrbStack, network, GUI, provider, model, GPU, or production
source change because the property under test is specifically Windows NTFS
path resolution.

**U.** This is one native-Windows construction fixture, not production
remediation, a symlink-race proof, a real broker file-read result, cross-OS
parity, or #3152 model-escalation acceptance. The candidate remains research
only; #4882 and #3152 stay open.
