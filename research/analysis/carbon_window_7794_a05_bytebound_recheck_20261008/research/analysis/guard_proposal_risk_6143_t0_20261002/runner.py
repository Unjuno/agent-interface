import argparse
import json
from fractions import Fraction

from simulator import analyze


def encode(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as handle:
        fixture = json.load(handle)
    result = encode(analyze(fixture))
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"schema": result["schema"], "cells": result["cells"], "controls": result["controls"]}, sort_keys=True))


if __name__ == "__main__":
    main()
