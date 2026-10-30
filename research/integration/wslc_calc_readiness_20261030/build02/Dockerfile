FROM agent-interface-xvfb-mcp:late-input-r19
USER root
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-calc openbox fonts-liberation tesseract-ocr tesseract-ocr-eng && dpkg-query -W > /opt/calc-ocr-packages.tsv && tesseract --version > /opt/tesseract-version.txt 2>&1
ENV SAL_USE_VCLPLUGIN=gen
