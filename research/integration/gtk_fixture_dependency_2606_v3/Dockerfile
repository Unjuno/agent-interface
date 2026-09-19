FROM python@sha256:e635facd4cd70a0e0b5d72cb0ce38f24434b6e98e11c2383d428a880c0f7232c
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends     python3-gi python3-xlib gir1.2-gtk-3.0 xvfb xauth     && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/usr/lib/python3/dist-packages
