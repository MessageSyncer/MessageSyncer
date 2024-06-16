from .base import *
from typing import List
import aiocron


@dataclass
class GetResult:
    user_id: str
    ts: int
    content: Struct


@dataclass
class GetterConfig(AdapterConfig):
    trigger: list[str] = field(default_factory=list)


@dataclass
class GetterInstanceConfig(AdapterInstanceConfig):
    pass


class Getter(Adapter[TADAPTERCONFIG, TADAPTERINSTANCECONFIG], Generic[TADAPTERCONFIG, TADAPTERINSTANCECONFIG]):
    def __init__(self, id=None) -> None:
        super().__init__(id)

        self._working = False
        self._first = True
        self._trigger: dict[str, aiocron.Cron] = {}
        self._number_of_consecutive_failures: int = 0

    @property
    def available(self):
        return not self._working

    @abstractmethod
    async def list(self) -> list[str]:
        """Get newest lists. Must be overrided.

        Returns:
            list[str]: Lists of ids.
        """
        pass

    @abstractmethod
    async def detail(self, id: str) -> GetResult:
        """Get detail of a specific id. Must be overrided.

        Args:
            id (str): id

        Returns:
            GetResult: Result
        """
        pass

    async def details(self, ids: List[str]) -> GetResult: 
        """Get detail of list of ids. Often used to merge multiple ids into a single message.

        Args:
            ids (list[str]): ids

        Returns:
            GetResult: Result
        """
        raise NotImplementedError()
