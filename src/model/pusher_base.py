from .base import *


@dataclass
class PusherConfig(AdapterConfig): ...


@dataclass
class PusherInstanceConfig(AdapterInstanceConfig): ...


class Pusher(
    Adapter[TADAPTERCONFIG, TADAPTERINSTANCECONFIG],
    Generic[TADAPTERCONFIG, TADAPTERINSTANCECONFIG],
):
    _default_config_type = PusherConfig
    _default_instanceconfig_type = PusherInstanceConfig

    @abstractmethod
    async def push(self, content: Struct, to: str = None) -> None: ...
