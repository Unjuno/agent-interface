FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-draw python3-uno python3 ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /work
ENTRYPOINT ["python3"]
