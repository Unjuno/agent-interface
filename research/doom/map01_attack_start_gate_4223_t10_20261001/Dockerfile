FROM --platform=linux/amd64 python:3.13.5-slim-bookworm@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      xvfb openbox xauth wmctrl libgl1 libglu1-mesa libglib2.0-0 libxext6 \
      libxrender1 libsm6 libopenal1 libsdl2-2.0-0 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY wheels/ /wheels/
RUN python -m pip install --no-index --no-deps /wheels/*.whl \
    && mkdir -p /opt/obstac /evidence \
    && dpkg-query -W -f='${Package}=${Version}\n' > /opt/obstac/dpkg-query.txt \
    && command -v wmctrl >/dev/null \
    && python -c 'import platform,sys,vizdoom; assert sys.version_info[:3] == (3,13,5); assert vizdoom.__version__ == "1.3.0"; assert platform.machine() == "x86_64"'
WORKDIR /tmp
