# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Union


KeyLike = Union[str, bytes]


class SignerBase(ABC):
    sign_type: str = ""

    @abstractmethod
    def sign(self, message: str) -> str:
        ...

    @abstractmethod
    def verify(self, message: str, signature: str, public_key) -> bool:
        ...


class EncryptorBase(ABC):
    encrypt_type: str = ""

    @abstractmethod
    def encrypt(
        self,
        plaintext: Union[str, bytes],
        key: Union[str, bytes],
        nonce: Union[str, bytes],
        aad: Union[str, bytes] = b"",
    ) -> str:
        ...

    @abstractmethod
    def decrypt(
        self,
        ciphertext: str,
        key: Union[str, bytes],
        nonce: Union[str, bytes],
        aad: Union[str, bytes] = b"",
    ) -> str:
        ...
