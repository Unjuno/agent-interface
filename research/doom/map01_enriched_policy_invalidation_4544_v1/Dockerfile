FROM python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9

ENV PYTHONDONTWRITEBYTECODE=1 \
    SDL_VIDEODRIVER=x11 \
    LIBGL_ALWAYS_SOFTWARE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates fonts-dejavu-core libasound2 libgl1 libgl1-mesa-dri \
       libglib2.0-0 libgomp1 libice6 libpulse0 libsm6 libx11-6 libxcomposite1 \
       libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxinerama1 \
       libxkbcommon0 libxrandr2 libxrender1 libxtst6 libxcb1 libxcb-cursor0 \
       libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
       libxcb-render-util0 libxcb-shape0 libxcb-shm0 libxcb-xfixes0 \
       openbox wmctrl x11-utils x11-xserver-utils xauth xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --disable-pip-version-check --no-cache-dir \
       vizdoom==1.3.0 numpy==1.26.4 Pillow==10.4.0 python-xlib==0.33 \
       openpyxl==3.1.5

RUN python -c 'import hashlib,pathlib,urllib.request,zipfile; url="https://github.com/freedoom/freedoom/releases/download/v0.13.0/freedoom-0.13.0.zip"; archive=pathlib.Path("/tmp/freedoom.zip"); archive.write_bytes(urllib.request.urlopen(url,timeout=60).read()); raw=archive.read_bytes(); assert hashlib.sha256(raw).hexdigest()=="3f9b264f3e3ce503b4fb7f6bdcb1f419d93c7b546f4df3e874dd878db9688f59"; z=zipfile.ZipFile(archive); wad=z.read("freedoom-0.13.0/freedoom2.wad"); assert hashlib.sha256(wad).hexdigest()=="a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"; target=pathlib.Path(__import__("vizdoom").__file__).parent/"freedoom2.wad"; target.write_bytes(wad); assert target.stat().st_size==28787748; archive.unlink()'

WORKDIR /src
CMD ["python3"]
