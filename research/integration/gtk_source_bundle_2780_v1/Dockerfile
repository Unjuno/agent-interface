FROM agent-interface-gtk-fixture-v2:2748
USER root
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    python3-xlib \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/usr/lib/python3/dist-packages
