FROM agent-interface-2972:20260920

RUN apt-get update \
    && apt-get -o APT::Keep-Downloaded-Packages=true --download-only install -y --no-install-recommends python3-tk=3.12.3-0ubuntu1 \
    && install -d /tmp/tk-xkb-debs \
    && cp /var/cache/apt/archives/*.deb /tmp/tk-xkb-debs/ \
    && apt-get install -y --no-install-recommends python3-tk=3.12.3-0ubuntu1 \
    && install -d /opt/tk-xkb-environment \
    && dpkg-query -W -f='${Package}=${Version}\n' > /opt/tk-xkb-environment/packages.txt \
    && sha256sum /tmp/tk-xkb-debs/*.deb > /opt/tk-xkb-environment/deb-sha256sums.txt \
    && python3 -c 'import tkinter; assert tkinter.TkVersion == 8.6' \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb /tmp/tk-xkb-debs
