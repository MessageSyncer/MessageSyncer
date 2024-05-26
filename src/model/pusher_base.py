from .base import *
from util import *


@dataclass
class PusherConfig(AdapterConfig):
    pass


@dataclass
class PusherInstanceConfig(AdapterInstanceConfig):
    pass


@dataclass
class PushResult:
    succeed: bool
    exception: Exception = None


class Pusher(Adapter[TADAPTERCONFIG, TADAPTERINSTANCECONFIG], Generic[TADAPTERCONFIG, TADAPTERINSTANCECONFIG]):
    @abstractmethod
    async def push(self, content: Struct, to: str) -> PushResult:
        pass
