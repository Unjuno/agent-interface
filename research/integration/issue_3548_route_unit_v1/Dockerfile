FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-xlib python3-pil xvfb openbox x11-utils x11-apps \
    ca-certificates fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install --break-system-packages --no-cache-dir mcp==1.30.0
WORKDIR /repo
