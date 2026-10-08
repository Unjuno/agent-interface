#!/usr/bin/env bash
set -euo pipefail

stage=${1:?usage: run_orbstack.sh construction|candidate|audit}
case "$stage" in
  construction|candidate|audit) ;;
  *) exit 64 ;;
esac

root=$(git rev-parse --show-toplevel)
rel=research/analysis/effect_terminal_feedback_6301_t0_successor_20261002
src="$root/$rel"
formal="$src/formal_03"
machine=effect-terminal-feedback-6301-t0-orbstack-20261002
image=sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f

git fetch origin main >/dev/null 2>&1
git merge-base --is-ancestor 9a573b00dc595e64d09387e567c85e10b61a46c1 origin/main
git merge-base --is-ancestor 9a573b00dc595e64d09387e567c85e10b61a46c1 HEAD
[[ $(git branch --show-current) == research/effect-terminal-feedback-6301-orbstack-t0b-20261002 ]]
[[ $(shasum -a 256 "$src/fixture.json" | cut -d' ' -f1) == 35bfa13d5edee93d834ddc54c980bb24a48b8a5bb9a4e9bcc9dcddd11d1b51a9 ]]
[[ $(shasum -a 256 "$src/candidate.py" | cut -d' ' -f1) == b41036c61ebece89a2f1b990e7ae2f9b896512fc2983b29a9b4dd9e712c9cc88 ]]
[[ $(shasum -a 256 "$src/auditor.py" | cut -d' ' -f1) == 831ad1e7a499b1d28bd5b0b9fbfb10b9f5409eddc47460e4a28209d84055977e ]]
[[ $(shasum -a 256 "$src/test_construction.py" | cut -d' ' -f1) == 5e206a9109b4c4442c3ba52facd14559c8241b339c8fbf648575da4377a7542a ]]
[[ $(orb -m "$machine" -u root docker image inspect "$image" --format '{{.Id}} {{.Os}}/{{.Architecture}}') == "$image linux/arm64" ]]

case "$stage" in
  construction)
    [[ ! -e "$formal/construction.started" ]]
    mkdir -m 0777 "$formal/construction_out"
    touch "$formal/construction.started"
    name=issue6350-orb03-construction
    out="$formal/construction_out"
    cmd=(sh -ec 'python -c '\''import pathlib,platform,sys; print("PYTHON",sys.version); print("PLATFORM",platform.platform()); print("CGROUP", {p:pathlib.Path(p).read_text().strip() for p in ("/sys/fs/cgroup/cpu.max","/sys/fs/cgroup/memory.max","/sys/fs/cgroup/pids.max")})'\''; python -m unittest -v test_construction.py')
    ;;
  candidate)
    [[ $(<"$formal/construction.exit") == 0 ]]
    [[ ! -e "$formal/candidate.started" ]]
    mkdir -m 0777 "$formal/candidate_out"
    touch "$formal/candidate.started"
    name=issue6350-orb03-candidate
    out="$formal/candidate_out"
    cmd=(python candidate.py fixture.json /out/candidate_result.json)
    ;;
  audit)
    [[ $(<"$formal/candidate.exit") == 0 ]]
    [[ -s "$formal/candidate_out/candidate_result.json" ]]
    [[ ! -e "$formal/audit.started" ]]
    mkdir -m 0777 "$formal/audit_out"
    touch "$formal/audit.started"
    name=issue6350-orb03-auditor
    out="$formal/audit_out"
    cmd=(python auditor.py fixture.json /in/candidate_result.json /out/audit_result.json)
    ;;
esac

mounts=(--mount "type=bind,src=$src,dst=/src,readonly")
if [[ "$stage" == audit ]]; then
  mounts+=(--mount "type=bind,src=$formal/candidate_out,dst=/in,readonly")
else
  mounts+=(--mount "type=bind,src=$out,dst=/out")
fi

set +e
orb -m "$machine" -u root docker run --name "$name" --pull=never --network none --cpus 0.25 --memory 512m --pids-limit 64 --read-only --cap-drop ALL --security-opt no-new-privileges:true --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --workdir /src "${mounts[@]}" "$image" "${cmd[@]}" >"$formal/$stage.stdout.log" 2>&1
result=$?
set -e
printf '%s\n' "$result" >"$formal/$stage.exit"
orb -m "$machine" -u root docker inspect "$name" >"$formal/$stage.container-inspect.json"
exit "$result"
