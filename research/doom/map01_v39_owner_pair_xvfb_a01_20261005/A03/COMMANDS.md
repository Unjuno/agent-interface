# A03 commands

Freeze SHA-256: `22fd6aaee73f1b580b4175a46aa5856a09020fd0b45b8b19c70612ffe6019364`

Candidate, invoked once (remote exit 0):

```sh
ssh 'research-59-v39-owner-pair-a01-20261005@orb' 'cd /home/taka/owner-pair-a03 && bash run_once.sh'
```

Auditor, invoked once after candidate exit 0 (remote exit 0):

```sh
ssh 'research-59-v39-owner-pair-a01-20261005@orb' 'cd /home/taka/owner-pair-a03 && test "$(cat results/candidate.exit)" = 0 && test ! -e results/A03/audit.json && python3 audit.py results/A03/raw.json > results/A03/audit.stdout 2> results/A03/audit.stderr; audit_rc=$?; printf "%s\n" "$audit_rc" > results/A03/audit.exit; test "$audit_rc" -eq 0'
```

The VM is OrbStack Ubuntu 24.04.5 arm64 with Python 3.12.3, Xvfb `2:21.1.12-1ubuntu1.8`, and python3-xlib `0.33-2`. Candidate and auditor were not rerun.
