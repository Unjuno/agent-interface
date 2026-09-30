#!/bin/sh
set -eu
python -B /src/runner.py --source /src/frozen-effective-controller.py --out /out --image-id "$IMAGE_ID" --source-blob 096adf9b60eaf6a31fe92c836f57d1a4d26b177e
python -B /src/audit.py --raw /out/raw.json
