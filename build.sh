#!/usr/bin/env bash
set -euo pipefail

rm -rf dist build *.egg-info
python3 -m pip install --upgrade build
python3 -m build
