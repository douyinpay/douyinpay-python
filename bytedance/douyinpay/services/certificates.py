# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from ..constants import GET_PLATFORM_CERTS_PATH
from .base import Service


class CertificateService(Service):
    def download_certificates(self, **kwargs):
        return self._get(GET_PLATFORM_CERTS_PATH, **kwargs)
