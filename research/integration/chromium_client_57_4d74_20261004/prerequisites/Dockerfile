FROM calc-heldout-3700-4d74:20261003
USER root
RUN apt-get update && apt-get install -y --no-install-recommends chromium && rm -rf /var/lib/apt/lists/*
RUN /usr/local/bin/python3 -m pip install --no-cache-dir jsonschema==4.25.1
RUN /usr/local/bin/python3 -c "import PIL,Xlib,jsonschema; print('runner dependencies available')" && chromium --version
ENV PYTHONDONTWRITEBYTECODE=1

