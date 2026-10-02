FROM tk-xkb-refresh-4664:20260927-01
USER root
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       openbox x11-utils x11-apps imagemagick tesseract-ocr fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /experiment
