FROM python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
 python3 python3-tk python3-xlib xvfb openbox x11-utils x11-apps x11-xkb-utils \
 imagemagick tesseract-ocr fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /experiment
USER 65534:65534
