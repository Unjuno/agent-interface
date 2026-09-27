# Shared-offset acquisition evidence — Issues #3984 / #3995

Research-only, not a production reader or queue. See [REPORT.md](REPORT.md).
#3995 completed one54-case Linux process experiment; frozen independent audit PASS,
108 recorded worker exits0, ten corruption controls rejected. Unchecked dup reads
exposed12 incomplete snapshots; extent checking refused12; positional pread returned
all36 complete responses. #3984's earlier shell127 STOP remains unchanged.

## Full evidence and offline revalidation

The six binary parts are one lossless XZ-compressed UTF-8 JSON file map, not a model
or executable archive. PACK.json binds ordered part sizes/hashes/Git blob IDs and the
expanded369-file denominator. `unpack.py` validates then writes a NEW directory;
it never executes study code or overwrites a destination. Trusted local unpack path
only; checksums are integrity commitments, not source authentication.

From this directory (use a new destination and audit output):

```sh
python -I -S -B unpack.py /tmp/f3a1-retained-review
cd /tmp/f3a1-retained-review/successor_02
python -I -S -B test_audit.py
python -I -S -B audit.py --input formal-01 --out /tmp/f3a1-retained-audit.json
cmp AUDIT.json /tmp/f3a1-retained-audit.json
```

These commands recheck old bytes only. Do NOT run execute_once.py/run.py against a
consumed identity. New experiments require separate preregistration and fresh output.
The capsule preserves all frozen sources,18 excluded construction cases,54 formal
cases,108 worker transcripts/exits, snapshots, supervisor/auditor receipts, original
command STOP and both freezes. The visible worker/vendor copies match capsule bytes.
PUBLICATION_CHECK.json records369 exact restored files, byte-identical re-audit,
eight tests and seven packaging corruption/occupied-output refusals.

Hash/command preregistration was public before formal execution (#3995 comment
5766604317); full source bytes are published retrospectively, not misrepresented as
a pre-experiment source commit. The same author wrote separate candidate and auditor;
this is not independent human review. No GUI/model/input/network experiment, ACK,
production promotion, performance benefit or global-roadmap completion follows.
