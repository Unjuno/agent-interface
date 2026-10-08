FROM sha256:865bfbcc86992769ec9b8311a2344b67c664639d96d7cf0d5c407df9c2c500ed
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-calc openbox fonts-liberation && pip install --no-cache-dir Pillow==11.3.0 && dpkg-query -W > /opt/calc-package-pins.tsv
ENV SAL_USE_VCLPLUGIN=gen
