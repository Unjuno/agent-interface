#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
rel=research/analysis/effect_terminal_feedback_6301_t0_successor_20261002
src="$root/$rel"
formal03="$src/formal_03"
formal04="$src/formal_04"
machine=effect-terminal-feedback-6301-t0-orbstack-20261002
image=sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
base=9a573b00dc595e64d09387e567c85e10b61a46c1

git fetch origin main >/dev/null 2>&1
git merge-base --is-ancestor "$base" origin/main
git merge-base --is-ancestor "$base" HEAD
[[ $(git branch --show-current) == research/effect-terminal-feedback-6301-orbstack-t0b-20261002 ]]
[[ $(shasum -a 256 "$src/fixture.json" | cut -d' ' -f1) == 35bfa13d5edee93d834ddc54c980bb24a48b8a5bb9a4e9bcc9dcddd11d1b51a9 ]]
[[ $(shasum -a 256 "$src/auditor.py" | cut -d' ' -f1) == 831ad1e7a499b1d28bd5b0b9fbfb10b9f5409eddc47460e4a28209d84055977e ]]
[[ $(shasum -a 256 "$formal03/candidate_out/candidate_result.json" | cut -d' ' -f1) == c6024886ab276f24a033c18c5446651eae3adb30bb58ed3c999c1b77595085e1 ]]
[[ $(orb -m "$machine" -u root docker image inspect "$image" --format '{{.Id}} {{.Os}}/{{.Architecture}}') == "$image linux/arm64" ]]
[[ $(<"$formal03/candidate.exit") == 0 ]]
[[ ! -e "$formal04/audit.started" ]]
[[ ! -e "$formal04/audit_out" ]]

mkdir -m 0755 "$formal04"
mkdir -m 0777 "$formal04/audit_out"
touch "$formal04/audit.started"
name=issue6350-orb04-auditor
set +e
orb -m "$machine" -u root docker run --name "$name" --pull=never --network none --cpus 0.25 --memory 512m --pids-limit 64 --read-only --cap-drop ALL --security-opt no-new-privileges:true --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --workdir /src --mount "type=bind,src=$src,dst=/src,readonly" --mount "type=bind,src=$formal03/candidate_out,dst=/in,readonly" --mount "type=bind,src=$formal04/audit_out,dst=/out" "$image" python auditor.py fixture.json /in/candidate_result.json /out/audit_result.json >"$formal04/audit.stdout.log" 2>&1
result=$?
set -e
printf '%s\n' "$result" >"$formal04/audit.exit"
orb -m "$machine" -u root docker inspect "$name" >"$formal04/audit.container-inspect.json"
exit "$result"
