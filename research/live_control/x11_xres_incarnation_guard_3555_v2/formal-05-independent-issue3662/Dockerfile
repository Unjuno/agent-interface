FROM agent-interface-3311-runtime-v2:20260920@sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc6-dev libx11-dev libxres-dev python3-tk x11-apps xauth \
    openbox wmctrl xdotool
COPY src/xres_owner.c /usr/local/src/xres_owner.c
RUN gcc -O2 -Wall -Wextra -Werror /usr/local/src/xres_owner.c -o /usr/local/bin/xres_owner -lXRes -lX11
WORKDIR /work
