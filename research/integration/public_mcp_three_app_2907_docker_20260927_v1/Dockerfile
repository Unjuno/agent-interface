FROM mixed-app-2499-xauth@sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3

COPY requirements-lock.txt /tmp/requirements-lock.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements-lock.txt \
    && python3 -c "import mcp, PIL, Xlib; print('mcp', mcp.__file__); print('Pillow', PIL.__version__); print('python-xlib', Xlib.__file__)"

WORKDIR /experiment
