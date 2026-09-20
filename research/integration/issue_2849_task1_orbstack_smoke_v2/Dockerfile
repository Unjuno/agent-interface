FROM mixed-formal-2992-debian:20260920

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq \
    docker.io=20.10.24+dfsg1-1+deb12u1+b6 \
    openbox=3.6.1-10 \
    python3-numpy=1:1.24.2-1+deb12u1 \
    python3-openpyxl=3.0.9-1 \
    python3-pil=9.4.0-1.1+deb12u1 \
    python3-pip=23.0.1+dfsg-1 \
    python3-xlib=0.33-2 \
    wmctrl=1.07-7+b1 && \
    rm -rf /var/lib/apt/lists/*

COPY python-schema-requirements.lock /tmp/python-schema-requirements.lock
RUN python3 -m pip install --break-system-packages --no-cache-dir --no-deps \
    -r /tmp/python-schema-requirements.lock && \
    rm /tmp/python-schema-requirements.lock

RUN mkdir -p /home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64 && \
    ln -s /usr/bin/chromium \
      /home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome

ENV DISPLAY=:99
WORKDIR /workspace
