FROM sha256:4b8e054511b1f3e3f4957ae657c20648f8e87312a75ebecafe2405bc6d852fd7
USER root
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-calc openbox fonts-liberation tesseract-ocr tesseract-ocr-eng && dpkg-query -W > /opt/calc-ocr-packages.tsv && tesseract --version > /opt/tesseract-version.txt 2>&1
ENV SAL_USE_VCLPLUGIN=gen
