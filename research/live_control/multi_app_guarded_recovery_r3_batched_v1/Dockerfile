FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    openbox \
    wmctrl \
    xterm \
    xvfb \
    x11-utils \
    xauth \
    strace \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir python-xlib==0.33
RUN mkdir -p /usr/local/share/r3 && \
    dpkg-query -W -f='${Package}=${Version}\n' > /usr/local/share/r3/packages.txt && \
    python --version > /usr/local/share/r3/python.txt && \
    chromium --version > /usr/local/share/r3/chromium.txt 2>&1 && \
    openbox --version > /usr/local/share/r3/openbox.txt 2>&1
ENTRYPOINT ["python", "-B"]
