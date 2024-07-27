from .base import *
from util import *


@dataclass
class PusherConfig(AdapterConfig):
    pass


@dataclass
class PusherInstanceConfig(AdapterInstanceConfig):
    pass


class Pusher(Adapter[TADAPTERCONFIG, TADAPTERINSTANCECONFIG], Generic[TADAPTERCONFIG, TADAPTERINSTANCECONFIG]):
    @abstractmethod
    async def push(self, content: Struct, to: str = None) -> None:
        pass
