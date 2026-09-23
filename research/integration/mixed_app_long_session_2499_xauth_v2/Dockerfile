FROM mixed-app-2794:local
USER root
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends xauth \
    && rm -rf /var/lib/apt/lists/*
