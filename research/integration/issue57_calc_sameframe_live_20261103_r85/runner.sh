#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export DISPLAY=:97 PYTHONPATH=/workspace
ATTEMPT_DIR="${ATTEMPT_DIR:?ATTEMPT_DIR must name the frozen arm}"
export EVIDENCE_DIR="/evidence/${ATTEMPT_DIR}"
mkdir -p "$EVIDENCE_DIR"
exec > >(tee -a "$EVIDENCE_DIR/container-runner.log") 2>&1
printf 'attempt_dir=%s\nstart_utc=%s\n' "$ATTEMPT_DIR" "$(date -u +%FT%TZ)"
timeout --signal=TERM --kill-after=5s 180s apt-get update > "$EVIDENCE_DIR/apt-update.log" 2>&1
timeout --signal=TERM --kill-after=5s 180s apt-get install -y --no-install-recommends libreoffice-calc=4:7.4.7-1+deb12u14 tesseract-ocr=5.3.0-2 python3-xlib x11-utils openbox > "$EVIDENCE_DIR/apt-install.log" 2>&1
dpkg-query -W -f='${Version}\n' libreoffice-core > "$EVIDENCE_DIR/package-version.txt"
dpkg-query -W -f='${Version}\n' tesseract-ocr > "$EVIDENCE_DIR/tesseract-version.txt"
printf 'image_os='; . /etc/os-release; printf '%s %s\n' "$ID" "$VERSION_ID"
printf 'python='; python3 --version
printf 'package_libreoffice='; cat "$EVIDENCE_DIR/package-version.txt"
printf 'package_tesseract='; cat "$EVIDENCE_DIR/tesseract-version.txt"
Xvfb "$DISPLAY" -screen 0 1280x800x24 -nolisten tcp > "$EVIDENCE_DIR/xvfb.log" 2>&1 & xvfb_pid=$!
openbox --sm-disable > "$EVIDENCE_DIR/openbox.log" 2>&1 & wm_pid=$!
cleanup_display() { kill "$wm_pid" "$xvfb_pid" 2>/dev/null || true; wait "$wm_pid" "$xvfb_pid" 2>/dev/null || true; }
trap cleanup_display EXIT
for _ in $(seq 1 100); do xdpyinfo -display "$DISPLAY" >/dev/null 2>&1 && break; sleep .1; done
xdpyinfo -display "$DISPLAY" >/dev/null
export OCR_GUARD_CONTROL=skip
timeout --signal=TERM --kill-after=10s 600s python3 "$EVIDENCE_DIR/experiment.py"
printf 'end_utc=%s\n' "$(date -u +%FT%TZ)"
