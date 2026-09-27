#!/bin/sh
set -eu
cd "$(dirname "$0")"
make clean test
./build/facility --bench --seed 424242 --episodes 500 --difficulty 0.6
