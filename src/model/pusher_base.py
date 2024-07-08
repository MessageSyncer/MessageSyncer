from .base import *
from util import *


@dataclass
class PusherConfig(AdapterConfig):
    pass


@dataclass
class PusherInstanceConfig(AdapterInstanceConfig):
    pass


class Pusher(Adapter[TADAPTERCONFIG, TADAPTERINSTANCECONFIG], Generic[TADAPTERCONFIG, TADAPTERINSTANCECONFIG]):
    __configtype__ = PusherConfig
    __instanceconfigtype__ = PusherInstanceConfig

    def __init__(self, id=None) -> None:
        super().__init__(id)

    @abstractmethod
    async def push(self, content: Struct, to: str) -> None:
        pass
