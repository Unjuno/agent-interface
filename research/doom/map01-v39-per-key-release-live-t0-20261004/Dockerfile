FROM python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9

ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 \
    SDL_VIDEODRIVER=x11 LIBGL_ALWAYS_SOFTWARE=1 OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates fonts-dejavu-core libasound2 libgl1 libgl1-mesa-dri \
       libglu1-mesa libsdl2-2.0-0 libopenal1 libglib2.0-0 libice6 libsm6 \
       libx11-6 libxext6 libxrender1 libxtst6 openbox wmctrl x11-utils \
       x11-xserver-utils xauth xvfb \
    && dpkg-query -W > /opt/dpkg-manifest.txt \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
       vizdoom==1.3.0 numpy==1.26.4 Pillow==10.4.0 \
       python-xlib==0.33 openpyxl==3.1.5 \
    && python -m pip freeze --all > /opt/python-manifest.txt

WORKDIR /tmp
CMD ["python3", "--version"]
