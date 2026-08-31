# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict

from . import paths
from .base import Service


class CashierService(Service):
    def prepay_consult(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PREPAY_CONSULT, data, **kwargs)
