# Frozen WSLc commands

Image is invoked by local image ID after verifying repository digest; pull is disabled.

Construction:
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume <checkout>:/src:ro --workdir /src sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4 python -B -m unittest discover -s /src -p test_*.py -v

Candidate (one invocation):
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 --volume <checkout>:/src:ro --volume <candidate-output>:/out --workdir /tmp sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4 python -B /src/candidate.py --fixture /src/fixture.json --out /out/candidate.raw.json

Auditor (one invocation after candidate exit 0):
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 --volume <checkout>:/src:ro --volume <candidate-output>:/results:ro --volume <audit-output>:/out --workdir /tmp sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4 python -B /src/auditor.py --fixture /src/fixture.json --oracle /src/oracle.json --raw /results/candidate.raw.json --out /out/audit.json
