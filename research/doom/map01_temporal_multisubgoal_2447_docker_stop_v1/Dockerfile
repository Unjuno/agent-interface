FROM python:3.13-slim@sha256:7c61056e61ac89e852de05f3dc6fa51a6dd2181797bceed46aa725dd7cb2cd3b

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libfontconfig1 libgl1 libglib2.0-0 libice6 libsm6 libx11-6 libxext6 \
      libxrender1 openbox openbox-lxde-session wmctrl x11-utils xauth xterm xvfb \
 && rm -rf /var/lib/apt/lists/*

COPY wheels /wheels
RUN python -m pip install --no-cache-dir --find-links=/wheels \
      numpy==2.5.3 Pillow==12.3.0 pygame-ce==2.5.8 python-xlib==0.33 \
      vizdoom==1.3.0 gymnasium==1.3.0 openpyxl==3.1.5 \
      opencv-python-headless==4.13.0.92 \
 && rm -rf /wheels

WORKDIR /work
