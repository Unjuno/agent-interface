FROM sha256:9e9b1a232f08b8c437834f8a40a5b39ca4be9c66b953833170930c70fdc66d89
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends xvfb xdotool xclip && apt-get clean
ENV QT_QPA_PLATFORM=xcb QT_XCB_GL_INTEGRATION=none
WORKDIR /src
ENTRYPOINT []
CMD []
