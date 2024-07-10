from abc import abstractmethod, ABC
from dataclasses import dataclass, asdict, field
from typing import TypeVar, Generic
from config import get_config_manager
import typing
from util import *
from .struct import Struct

TADAPTERCONFIG = TypeVar('TADAPTERCONFIG', bound='AdapterConfig')
TADAPTERINSTANCECONFIG = TypeVar('TADAPTERINSTANCECONFIG', bound='AdapterInstanceConfig')


@dataclass
class AdapterConfig():
    pass


@dataclass
class AdapterInstanceConfig():
    pass


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

        if id != None:
            self.name += f'.{id}'

        _generic_params = self._get_generic_params()

        def _process_type(_i, _T):
            _t = _generic_params[_i]
            if _t == _T:
                _t = dict
            return _t

        self._config = get_config_manager(_process_type(0, TADAPTERCONFIG), self.class_name)
        if self.id != None:
            self._instance_config = get_config_manager(_process_type(1, TADAPTERINSTANCECONFIG), self.name)
        else:
            self._instance_config = None

        self.logger = logging.getLogger(self.name)

    @property
    def config(self) -> TADAPTERCONFIG:
        return self._config.value

    @property
    def instance_config(self) -> TADAPTERINSTANCECONFIG:
        if self._instance_config != None:
            return self._instance_config.value
        else:
            return {}

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)
