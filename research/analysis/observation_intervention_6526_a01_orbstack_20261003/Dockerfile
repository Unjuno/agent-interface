FROM ubuntu:24.04@sha256:a853f94d226358a79c740cfc7bce0c289748f3fe3488d921d038ccd752c61b60
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-tk xvfb x11-apps x11-utils xauth ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /study
ENTRYPOINT ["python3", "-B", "/src/candidate.py"]
