FROM agent-interface-map01-clock-review-fixed:20260920
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git libboost-all-dev libsdl2-dev libopenal-dev \
    python3-dev pkg-config ca-certificates binutils \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch 1.3.0 --recurse-submodules \
      https://github.com/Farama-Foundation/ViZDoom.git /tmp/vizdoom-src \
    && test "$(git -C /tmp/vizdoom-src rev-parse HEAD)" = \
      c8e0a31182d98c6f40a65674283e736b851e8e59 \
    && git -C /tmp/vizdoom-src submodule update --init --recursive
COPY vizdoom-tic-counter-v1.patch /tmp/vizdoom-tic-counter-v1.patch
RUN git -C /tmp/vizdoom-src apply /tmp/vizdoom-tic-counter-v1.patch \
    && python -m pip install --no-cache-dir /tmp/vizdoom-src \
    && python -c 'import vizdoom; print(vizdoom.__version__, vizdoom.__file__)'
WORKDIR /probe
COPY counter_call.c /counter_call.c
RUN gcc -shared -fPIC -O2 $(python3-config --includes) \
    -o /counter_call$(python3-config --extension-suffix) /counter_call.c
RUN mkdir -p /opt/vizdoom-counter-audit \
    && cp /tmp/vizdoom-src/src/vizdoom/src/CMakeFiles/vizdoom.dir/viz_main.cpp.o \
       /opt/vizdoom-counter-audit/viz_main.cpp.o
COPY probe.py /probe48.py
ENTRYPOINT ["python", "/probe48.py"]
