FROM mixed-app-identity-2782-local@sha256:e6ced3789130dae21c7b42b7b9d25cd590a271a77910e16c01d2edf87e44cee6
USER root
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends openbox wmctrl xauth \
    && rm -rf /var/lib/apt/lists/*
ENTRYPOINT []
