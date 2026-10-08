FROM ubuntu@sha256:a853f94d226358a79c740cfc7bce0c289748f3fe3488d921d038ccd752c61b60
ENV DEBIAN_FRONTEND=noninteractive QT_QPA_PLATFORM=offscreen QT_LOGGING_RULES="qt.qpa.*=false" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pyqt5 && rm -r /var/lib/apt/lists/*
WORKDIR /src
ENTRYPOINT ["/usr/bin/python3", "-B"]
