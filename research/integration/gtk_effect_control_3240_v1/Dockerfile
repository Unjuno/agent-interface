FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9

ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    python3-gi gir1.2-gtk-3.0 python3-xlib xvfb xauth x11-utils x11-apps \
 && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/usr/lib/python3/dist-packages
WORKDIR /repo
CMD ["python", "--version"]
