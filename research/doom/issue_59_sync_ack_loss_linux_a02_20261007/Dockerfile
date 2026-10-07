FROM python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1
COPY requirements.lock /opt/requirements.lock
RUN python -m pip install --no-cache-dir --only-binary=:all: -r /opt/requirements.lock \
 && python -m pip freeze --all > /opt/python-manifest.txt \
 && mkdir -p /workspace/research/live_control /workspace/research/doom /out
