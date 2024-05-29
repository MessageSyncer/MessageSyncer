from util import *
from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, Type
path = Path() / '../data' / 'config'
path.mkdir(parents=True, exist_ok=True)
T = TypeVar('T')
T1 = TypeVar('T1')


class HotReloadConfigManager(Generic[T]):
    def __init__(self, config_type: T, config_path: Path) -> None:
        self._last_config: config_type
        self._last_hash = None
        self.config_type = config_type
        self.config_path = config_path

    @property
    def value(self) -> T:
        if self.config_path.exists():
            config = read_file(self.config_path)
            write_back = True
        else:
            self.config_path.touch()
            config = "{}"
            write_back = False
        write_back = True

        now_hash = hash(config)
        if now_hash == self._last_hash:
            return self._last_config
        self._last_hash = now_hash

        config = yaml.safe_load(config)

        def from_dict(data_type: T, data: dict) -> T:  
            # TODO: remove dict access support
            # FIXME: check
            """Instantiate data classes from dictionaries, including working with nested data classes."""

            if data_type in [dict,int,str,list,float,None]:
                return data
            
            try:
                if data_type.__origin__ in [dict,list]:
                    return data
            except:
                pass

            def dict_access():
                """
                The shift from using dict as the profile type to using dataclass as the profile type is a disruptive change from Pusher to MessageSyncer.

                To be compatible with all adapters, MessageSyncer supports accessing dataclass instances like accessing dict through the following code.

                This feature will be removed one day in the future. It is not recommended that any adapter developer continue to use dict as a configuration file type. Migrate to dataclass as soon as possible.
                """

                def __getter__(self: object, key, default=None):
                    try:
                        return self.__getattribute__(key)
                    except AttributeError as e:
                        return default

                def get(self, key, default=None):
                    return self.__getter__(key, default)

                def __getitem__(self, key):
                    return self.__getter__(key)

                data_type.__getter__ = __getter__
                data_type.get = get
                data_type.__getitem__ = __getitem__

                return data_type

            dict_access()
            fieldtypes = {f.name: f.type for f in data_type.__dataclass_fields__.values()}
            obj = data_type(**{f: from_dict(fieldtypes[f], data[f]) if isinstance(data[f], dict) else data[f] for f in data})

            return obj

        config = from_dict(self.config_type, config)

        if write_back:
            if self.config_type != dict:  # TODO: remove dict access support
                write_back_config = asdict(config)
            else:
                write_back_config = config
            write_yaml(self.config_path, write_back_config)

        self._last_config = config
        return config


def get_config_manager(config_type: Type[T], name) -> HotReloadConfigManager[T]:
    config_file = path / f'{name}.yaml'
    return HotReloadConfigManager(config_type, config_file)


@dataclass
class MainConfig:
    @dataclass
    class LoggingConfig:
        verbose: bool = False

    @dataclass
    class APIConfig:
        token: list[str] = field(default_factory=list[str])
        port: int = 11589

    pair: list[str] = field(default_factory=list[str])
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    api: APIConfig = field(default_factory=APIConfig)
    refresh_when_start: bool = True
    first_get_donot_push: bool = True
    block: list[str] = field(default_factory=list[str])
    perf_merged_details: list[str] = field(default_factory=list[str])
    proxies: dict[str, str] = field(default_factory=dict[str, str])  # This field will be passed directly to requests.request


main_manager = get_config_manager(MainConfig, 'main')
main = main_manager.value
verbose = main.logging.verbose
