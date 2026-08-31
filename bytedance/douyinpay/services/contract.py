# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict

from . import paths
from .base import Service


class ContractService(Service):
    def query_contract(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.QUERY_CONTRACT, data, **kwargs)

    def delete_contract(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.DELETE_CONTRACT, data, **kwargs)

    def pre_entrust_web(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PRE_ENTRUST_WEB, data, **kwargs)

    def h5_entrust_web(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.H5_ENTRUST_WEB, data, **kwargs)
