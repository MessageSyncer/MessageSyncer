from typing import List, Union

import aiocron

from .base import *


@dataclass
class GetResult:
    user_id: str
    ts: int
    content: Struct


@dataclass
class GetterConfig(AdapterConfig):
    trigger: list[str] = field(
        default_factory=list
    )  # Partially supports hotreload. Takes effect after every time refreshes.


@dataclass
class GetterInstanceConfig(AdapterInstanceConfig):
    override_trigger: Union[list[str], None] = field(default=None)


class Getter(
    Adapter[TADAPTERCONFIG, TADAPTERINSTANCECONFIG],
    Generic[TADAPTERCONFIG, TADAPTERINSTANCECONFIG],
):
    _default_config_type = GetterConfig
    _default_instanceconfig_type = GetterInstanceConfig

    def __init__(self, id=None) -> None:
        super().__init__(id)

        self._working = False
        self._first = True
        self._triggers: dict[str, aiocron.Cron] = {}
        self._consecutive_failures_number: int = 0

    @property
    def available(self):
        return not self._working

    @abstractmethod
    async def list(self) -> list[str]:
        """Get newest lists. Must be overrided.

        Returns:
            list[str]: Lists of ids.
        """
        ...

    @abstractmethod
    async def detail(self, id: str) -> GetResult:
        """Get detail of a specific id. Must be overrided.

        Args:
            id (str): id

        Returns:
            GetResult: Result
        """
        ...

    async def details(self, ids: List[str]) -> GetResult:
        """Get detail of list of ids. Often used to merge multiple ids into a single message.

        Args:
            ids (list[str]): ids

        Returns:
            GetResult: Result
        """
        raise NotImplementedError()
