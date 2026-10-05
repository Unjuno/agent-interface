# A05 commands

Freeze SHA-256: `63288ade101470e925fbdceddcca8c2bf6dcc77091efae2270e6ea47a88b82c1`

Candidate, invoked once (remote exit 0):

```sh
ssh 'research-59-v39-owner-pair-a01-20261005@orb' 'cd /home/taka/owner-pair-a05 && bash run_once.sh'
```

Auditor, invoked once after candidate exit 0 (remote exit 0):

```sh
ssh 'research-59-v39-owner-pair-a01-20261005@orb' 'cd /home/taka/owner-pair-a05 && test "$(cat results/candidate.exit)" = 0 && test ! -e results/A05/audit.json && python3 audit.py results/A05/raw.json > results/A05/audit.stdout 2> results/A05/audit.stderr; audit_rc=$?; printf "%s\n" "$audit_rc" > results/A05/audit.exit; test "$audit_rc" -eq 0'
```

VM: OrbStack Ubuntu 24.04.5 arm64, Python 3.12.3, Xvfb `2:21.1.12-1ubuntu1.8`, python3-xlib `0.33-2`. Neither candidate nor auditor was rerun.
