import typing
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Generic, TypeVar

import log
from config import get_config_manager

from .struct import Struct

TADAPTERCONFIG = TypeVar("TADAPTERCONFIG", bound="AdapterConfig")
TADAPTERINSTANCECONFIG = TypeVar(
    "TADAPTERINSTANCECONFIG", bound="AdapterInstanceConfig"
)


@dataclass
class AdapterConfig: ...


@dataclass
class AdapterInstanceConfig: ...


class Adapter(ABC, Generic[TADAPTERCONFIG, TADAPTERINSTANCECONFIG]):
    def _get_generic_params(self):
        bases = self.__class__.__orig_bases__
        for base in bases:
            if isinstance(base, typing._GenericAlias):
                return base.__args__

    def __init__(self, id=None) -> None:
        super().__init__()
        self.id = id
        self.class_name = self.__class__.__name__
        self.name = self.class_name

        if id is not None:
            self.name += f".{id}"

        self.class_storage_path = Path() / "data" / "storage" / self.class_name
        self.storage_path = Path() / "data" / "storage" / self.name
        self.class_storage_path.mkdir(parents=True, exist_ok=True)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        _generic_params = self._get_generic_params()

        def _process_type(index, T, default):
            type_ = _generic_params[index]
            if type_ == T:
                type_ = default
            return type_

        self.config_manager = get_config_manager(
            _process_type(0, TADAPTERCONFIG, self._default_config_type), self.class_name
        )
        if self.id is not None:
            self.instance_config_manager = get_config_manager(
                _process_type(
                    1, TADAPTERINSTANCECONFIG, self._default_instanceconfig_type
                ),
                self.name,
            )
        else:
            self.instance_config_manager = None

        self.logger = log.getLogger(self.name)

    @property
    def config(self) -> TADAPTERCONFIG:
        return self.config_manager.value

    @property
    def instance_config(self) -> TADAPTERINSTANCECONFIG:
        if self.instance_config_manager is not None:
            return self.instance_config_manager.value
        else:
            return None

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)
