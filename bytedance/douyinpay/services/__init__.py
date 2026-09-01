# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from .base import Service


class DouyinPayServices(Service):
    """Thin generic service entry for merchant-supplied paths and params."""


__all__ = [
    "Service",
    "DouyinPayServices",
]
