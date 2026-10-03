# Additive retention preparation, not native successor completion

Addresses A01 audit retention gap without changing/replaying A01. Public PR7263
head0eec0872290d3f9c4f9fd24458da33796b05e917 remains unchanged during review.
These files are untracked local preparation and are not yet PR evidence.

H: a separate supervisor can reserve an attempt before ordinary child startup,
retain stderr and terminal after nonzero/timeout, and refuse reuse before a
second child's side effect. T: three real subprocess construction tests, no
native/game/model. D: reserve file exists; matching terminal JSON; nonzero1 and
raw startup-fault stderr; timeout terminal; reused output refuses before touch.
C/U: supervisor SIGKILL/host death, fsync durability, disk-full/permission faults,
descendant processes and exceptional supervisor teardown remain unverified;
attempt-only can be incomplete, not success. No unconditional retention claim.

First host command python3 -B -m unittest discover -s this directory -v: exit1,
3 missing-module errors before implementation. After minimal supervisor, same
command3PASS/exit0 (0.209s). Actual private OrbStack construction container
owner-retention-construction-5ce3-20261004 runs unchanged3tests: first3PASS/exit0,
0.125s; raw CONTAINER_CI.txt and full CONTAINER_TERMINAL.json retained. Exact
image200f0ba1c5b6689261b30f1cc89c26da1b8c8b522fbcbe27b688d55ea67348c5,
read-only /tests/source/root, networknone, requested1CPU512MiBswap512/PIDs128,
/tmp64MiB. Resource enforcement unmeasured. This is repeatable construction CI,
not a consumed formal/native allocation. Existing A01 result remains immutable.

Only own VM research-59-hud-ocr-5ce3-20261003/private Engine used; after CI,
Engine0running and exactVMstop command exited0. Still need independent review,
fresh native successor protocol, full post-close bitmap/events and runtime source
custody before claiming the A01 missing gates addressed experimentally.
