FROM debian:bookworm-slim AS build
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libx11-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY Makefile ops_world.h ops_world.c ops_world_part_00.inc ops_world_part_01.inc ops_world_part_02.inc ops_world_part_03.inc main.c test_ops_world.c render_fixtures.c ./
RUN make clean all && ./test_ops_world

FROM debian:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends libx11-6 xvfb xauth \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/ops_world /usr/local/bin/ops_world
WORKDIR /work
# Default container execution owns its X server instead of assuming DISPLAY exists.
ENTRYPOINT ["xvfb-run", "-a", "/usr/local/bin/ops_world"]
CMD ["--runtime", "60", "--report", "/work/report.json"]
