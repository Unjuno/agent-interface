set -euo pipefail
mkdir -p /tmp/adapter-bin /root/.codex /tmp/pycache
printf "#!/bin/sh\nexec env -u XAUTHORITY /usr/bin/Xvfb \"$@\"\n" > /tmp/adapter-bin/Xvfb
printf "#!/bin/sh\nif [ \"$1\" = \"-w\" ]; then shift; fi; printf \"%s\\n\" \"$1\"\n" > /tmp/adapter-bin/wslpath
chmod +x /tmp/adapter-bin/Xvfb /tmp/adapter-bin/wslpath
export PATH=/tmp/adapter-bin:/usr/local/bin:$PATH CODEX_HOME=/root/.codex PYTHONPYCACHEPREFIX=/tmp/pycache PYTHONPATH=/src/_vizdoom:/src/research/doom:/src/research/live_control
python3 -B /src/research/doom/map01_overlap_controller_v39.py --out /out/raw --iterations 6 --seed 991044 --session-span 6 --model gpt-6.1-sol --effort medium --measurement-session --load-fixture-manifest /out/construction-setup-a23/fixture.json
