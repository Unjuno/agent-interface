FROM python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 XAUTHORITY=/dev/null
RUN apt-get update && apt-get install -y --no-install-recommends xvfb && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir --disable-pip-version-check python-xlib==0.33
WORKDIR /study/SOURCE
