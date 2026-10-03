ARG BASE_IMAGE
FROM ${BASE_IMAGE}
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-pil tesseract-ocr tesseract-ocr-eng && apt-get clean && dpkg-query -W
ENV PYTHONDONTWRITEBYTECODE=1 OMP_THREAD_LIMIT=1
WORKDIR /tmp
ENTRYPOINT ["python3"]
