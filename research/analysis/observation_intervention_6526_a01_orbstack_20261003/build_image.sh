#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker pull --platform linux/arm64 ubuntu:24.04@sha256:a853f94d226358a79c740cfc7bce0c289748f3fe3488d921d038ccd752c61b60
docker build --pull=false --network=host -t issue6526-a01:construction .
docker run --rm --pull=never --network=none --entrypoint dpkg-query issue6526-a01:construction -W -f='${Package}=${Version}\n' > package-inventory.txt
docker image inspect issue6526-a01:construction --format '{{.Id}} {{.Os}}/{{.Architecture}} {{.Size}}'
docker image save -o /tmp/issue6526-a01-construction.tar issue6526-a01:construction
orbctl push -m research-6526-observer-a01-20261003 /tmp/issue6526-a01-construction.tar /home/taka/issue6526-build/issue6526-a01-construction.tar
orb -m research-6526-observer-a01-20261003 sudo docker image load -i /home/taka/issue6526-build/issue6526-a01-construction.tar
orb -m research-6526-observer-a01-20261003 sudo docker image inspect issue6526-a01:construction --format '{{.Id}} {{.Os}}/{{.Architecture}} {{.Size}}'
