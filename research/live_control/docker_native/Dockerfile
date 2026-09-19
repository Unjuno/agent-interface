FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pil python3-numpy python3-openpyxl python3-xlib \
    xvfb openbox wmctrl x11-utils xauth \
    inkscape libreoffice-calc fonts-dejavu-core ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/repo:/repo/research/live_control \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /repo
CMD ["sleep", "infinity"]
