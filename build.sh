#!/usr/bin/env bash
# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

rm -rf dist build *.egg-info
python3 -m pip install --upgrade build
python3 -m build
