FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libx11-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY facility.h facility_internal.h facility_world.c facility_tasks.c facility_render.c facility_misc.c main.c core_tests.c Makefile ./
RUN make clean all

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libx11-6 xvfb xauth python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /facility
COPY --from=build /src/facility /facility/facility
COPY --from=build /src/core_tests /facility/core_tests
COPY tests /facility/tests
COPY FIXED_SUITE.json sweep.py /facility/
COPY gui_smoke.sh run_tests_container.sh /facility/
ENV PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["/facility/facility"]
