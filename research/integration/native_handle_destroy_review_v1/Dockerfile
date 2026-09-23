FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq xvfb openbox git procps x11-utils && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir Pillow==10.2.0 python-xlib==0.33
WORKDIR /src
ENTRYPOINT []
