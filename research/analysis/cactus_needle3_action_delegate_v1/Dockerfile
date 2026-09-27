FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9

ENV NEEDLE_TELEMETRY=0 \
    DO_NOT_TRACK=1 \
    HF_HUB_DISABLE_PROGRESS_BARS=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY runtime-requirements.txt ./
RUN python -m pip install --no-cache-dir --disable-pip-version-check -r runtime-requirements.txt

WORKDIR /opt/experiment
COPY runner.py audit.py test_runner.py PREREGISTRATION.md FREEZE.json runtime-requirements.txt ./

ENTRYPOINT ["python", "runner.py"]
