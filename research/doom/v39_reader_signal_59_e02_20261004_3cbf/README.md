# E02: typed reader-failure candidate, parent #59

This is an additive successor experiment to E01/PR7220, not E01 replay and not
production adoption. Main/startup/wait owners (PR6944/7084) are untouched.
Current intake main2757ece00 plus fresh local b84fc9a4; README/ROADMAP/goal hashes
unchanged. Open/closed issue+PR and branches refreshed; bounded searches of v39
reader/parse and latest #59 comments found no focused competing repair.

## H/T/D/C/U

- H: catching a reader Exception and transporting its typed private exception
  object in the same FIFO lets wait retain the original cause without discarding
  queued normal events. E01 proved the missing communication boundary.
- T: new six-cell native allocation: healthy E02 ready; truncated JSON `{"event":`;
  ready followed by the fault only after a parent CONTINUE handshake; JSON `[1]`;
  invalid UTF8 `ff0a`; clean reader EOF while peer remains alive. Exact full source
  candidate differs at only two literal sites, inverse restores every original
  byte. Execute extracted local class/reader/wait, real owned pipes and children.
- D: candidate signal reaches wait with JSONDecodeError/UnicodeDecodeError cause,
  first ready retained before later fault, healthy ready retained; array remains
  TypeError, normal EOF remains TimeoutError (explicit unresolved controls). All
  peer identities/checkpoints/clean exits/retired readers must close. Scientific
  disagreement HOLD, missing custody STOP, no retries, first outcomes retained.
- C: source byte/inverse closure; E02 emitter receipts with successful byte counts
  (not raw stdout readback), actual cause doc/object; typed rows/PPID/UID/cgroups;
  independent saved-only scorer after complete exit0. Read-only source, own Engine.
- U: only receiver-error notification repaired. EOF, schema shape validation,
  full controller cleanup/recovery, queued-event expiry and live task effect remain
  open. Timeout .35s override, no default40s/harddeadline/causal speed claim. Reader
  join after fault precedes checkpoint and is recorded, not elapsed wait duration.
  Popen uses explicit strict UTF8 in this diagnostic. No game/model/native input.

Research unit one actual candidate-only six-cell experiment, saved audit1/retry0.
Allocation E02-59-20261004-3CBF, own research-6183-t0-20261003 VM/Engine; CPU1,
memory512MiB/swap0/pids64/nonroot501/networknone/read-only root+source/capdropALL.
No physical-host exclusive claim. Frozen full candidate is inert `.py.txt`, so it
cannot silently replace production v39 or conflict with committee-owned changes.
Independent integration/application and real controller adoption required later.

Roadmap: prior D03 HOLD and E01 diagnostic retained; current live threat/control,
independent useful feedback, same-model efficiency/human tempo and release gates
remain open. This repairs a concrete boundary, not those broader research gates.
