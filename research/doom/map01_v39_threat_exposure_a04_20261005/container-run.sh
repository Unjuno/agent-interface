#!/bin/bash
set -euo pipefail
mkdir -p /tmp/adapter-bin /root/.codex
cat > /tmp/adapter-bin/Xvfb <<'SH'
#!/bin/sh
exec env -u XAUTHORITY /usr/bin/Xvfb "$@"
SH
chmod +x /tmp/adapter-bin/Xvfb
export PATH="/tmp/adapter-bin:$PATH"
export CODEX_HOME=/root/.codex
exec env PYTHONPATH=/src/_vizdoom:/src/research/doom:/src/research/live_control python3 -B /src/research/doom/map01_overlap_controller_v39.py --out /out/map01-v39-threat-currentmain-a04/raw --iterations 6 --seed 991034 --session-span 6 --model gpt-6.1-sol --effort medium --measurement-session --load-fixture-manifest /out/construction-setup-a23/fixture.json
