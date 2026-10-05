FROM python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
ENV DEBIAN_FRONTEND=noninteractive PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
RUN cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max /sys/fs/cgroup/pids.max \
 && apt-get update \
 && apt-get install -y --no-install-recommends xvfb libgl1 libglu1-mesa libsdl2-2.0-0 libopenal1 libxtst6 \
 && dpkg-query -W > /opt/dpkg-manifest.txt
COPY requirements.txt /opt/requirements.txt
RUN python -m pip download --only-binary=:all: --dest /opt/wheels -r /opt/requirements.txt \
 && sha256sum /opt/wheels/* > /opt/wheels.sha256 \
 && python -m pip install --no-index --find-links /opt/wheels -r /opt/requirements.txt \
 && python -m pip freeze --all > /opt/python-manifest.txt
CMD ["python", "--version"]
