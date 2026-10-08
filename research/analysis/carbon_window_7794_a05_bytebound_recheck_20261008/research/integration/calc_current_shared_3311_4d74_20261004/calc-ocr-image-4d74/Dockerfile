FROM calc-heldout-3700-4d74:20261003
USER root
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng
RUN tesseract --version > /opt/tesseract-version.txt 2>&1 && dpkg-query -W > /opt/ocr-packages.txt
