FROM agent-interface-map01-clock-review-fixed:20260920
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git libboost-all-dev libsdl2-dev libopenal-dev \
    python3-dev pkg-config ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch 1.3.0 --recurse-submodules \
      https://github.com/Farama-Foundation/ViZDoom.git /tmp/vizdoom-src \
    && test "$(git -C /tmp/vizdoom-src rev-parse HEAD)" = \
      c8e0a31182d98c6f40a65674283e736b851e8e59 \
    && git -C /tmp/vizdoom-src submodule update --init --recursive
COPY vizdoom-tic-entry-v2.patch /tmp/vizdoom-tic-entry-v2.patch
RUN git -C /tmp/vizdoom-src apply /tmp/vizdoom-tic-entry-v2.patch \
    && python -m pip install --no-cache-dir /tmp/vizdoom-src \
    && python -c 'import vizdoom; print(vizdoom.__version__, vizdoom.__file__)'
WORKDIR /opt/phase-probe
COPY probe.py /probe.py
ENTRYPOINT ["python", "/probe.py"]
