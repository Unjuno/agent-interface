FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-gi python3-xlib python3-pil gir1.2-gtk-3.0 xvfb x11-utils ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /repo
ENTRYPOINT ["python3"]
