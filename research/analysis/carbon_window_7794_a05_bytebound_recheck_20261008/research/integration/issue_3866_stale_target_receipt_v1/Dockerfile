FROM agent-interface-x11-integration:20260921

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-calc python3-uno python3-xlib python3-openpyxl \
    xdotool wmctrl openbox xauth x11-utils dbus-x11 \
 && rm -rf /var/lib/apt/lists/*

CMD ["/usr/bin/python3", "--version"]

