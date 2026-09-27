FROM debian:bookworm-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/facility
COPY . /opt/facility
RUN make clean test
RUN ./build/facility --bench --seed 424242 --episodes 120 --difficulty 0.6

FROM debian:bookworm-slim AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/facility
COPY --from=build /opt/facility /opt/facility
ENV PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["./build/facility"]
CMD ["--stdio", "--seed", "424242", "--difficulty", "0.5"]
