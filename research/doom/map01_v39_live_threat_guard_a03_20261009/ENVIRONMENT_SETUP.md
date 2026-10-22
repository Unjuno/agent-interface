# A03 runtime setup, before the formal allocation

The dedicated OrbStack VM was already running, but the old temporary `/tmp/vizdoom-venv` and its WAD were absent. No game was initialized, no model request was sent, and no experiment output directory was created during this setup.

The VM's Ubuntu Noble arm64 image already had Python 3.12.3, `python3.12-venv`, Xvfb, `xauth`, and `x11-utils`. I recreated only the disposable environment with:

```sh
python3 -m venv /tmp/vizdoom-venv
/tmp/vizdoom-venv/bin/python -m pip install --no-cache-dir 'vizdoom==1.3.0'
```

The installed versions were `vizdoom==1.3.0`, `numpy==2.5.3`, `gymnasium==1.4.0`, `pygame-ce==2.5.8`, `cloudpickle==3.1.2`, `Farama-Notifications==0.0.6`, `typing_extensions==4.16.0`, and `pip==24.0`. Importing ViZDoom succeeded without creating a game. The bundled `freedoom2.wad` SHA-256 is `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`, matching the frozen MAP01 fixture's required WAD identity.

The exact display preflight command was:

```sh
xvfb-run -a -s '-screen 0 1280x800x24 -nolisten tcp' xdpyinfo
```

It succeeded and reported one 1280×800, 24-bit X11 screen. The formal launcher repeats this preflight before writing `FREEZE.json`, then runs the guest under the same `xvfb-run` arguments. No TCP listener or Docker container is used.

ViZDoom 1.3.0 was pinned because this retained fixture requires that exact version and WAD hash. The official [ViZDoom 1.3.0 release](https://github.com/Farama-Foundation/ViZDoom/releases) and [installation documentation](https://github.com/Farama-Foundation/ViZDoom#python-quick-start) list Linux ARM64 wheel support for modern Python; the actual installed package, import, and WAD digest are rechecked and written into the formal freeze immediately before launch.
