FROM python:3.12-slim
RUN apt-get update -qq && apt-get install -y -qq xvfb openbox xterm wmctrl libgl1 libglu1-mesa libx11-6 libxext6 libxrender1 libxrandr2 libxi6 libxxf86vm1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy pillow openpyxl python-xlib vizdoom==1.2.3
WORKDIR /workspace
