from util import *
from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, Type
path = Path() / '../data' / 'config'
path.mkdir(parents=True, exist_ok=True)
T = TypeVar('T')
T1 = TypeVar('T1')


class HotReloadConfigManager(Generic[T]):
    def __init__(self, config_type: T, config_path: Path) -> None:
        self.config_type = config_type
        self.config_path = config_path

    def allow_dict_access(data_type):
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

    def from_dict(data_type: T, data: dict) -> T:
        # TODO: remove dict access support
        # FIXME: check
        """Instantiate data classes from dictionaries, including working with nested data classes."""

        if data_type in [dict, int, str, list, float, None]:
            return data

        try:
            if data_type.__origin__ in [dict, list]:
                return data
        except:
            pass

        HotReloadConfigManager.allow_dict_access(data_type)
        fieldtypes = {f.name: f.type for f in data_type.__dataclass_fields__.values()}
        obj = data_type(**{f: HotReloadConfigManager.from_dict(fieldtypes[f], data[f]) if isinstance(data[f], dict) else data[f] for f in data if f in fieldtypes})

        return obj

    def asdict(self, config):
        if self.config_type != dict:  # TODO: remove dict access support
            dict_config = asdict(config)
        else:
            dict_config = config
        return dict_config

    def asyaml(self, config):
        return yaml.safe_dump(self.asdict(config))

    def save(self, config):
        write_file(self.config_path, self.asyaml(config))

    def yaml(self):
        if self.config_path.exists():
            config = read_file(self.config_path)
        else:
            self.config_path.touch()
            config = "{}"
        return config

    def dict(self):
        return yaml.safe_load(self.yaml())

    @property
    def value(self) -> T:
        yaml_config = self.yaml()
        dict_config = yaml.safe_load(yaml_config)
        config = HotReloadConfigManager.from_dict(self.config_type, dict_config)
        if self.asyaml(config) != yaml_config:
            self.save(config)
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

    @dataclass
    class Warning:
        to: list[str] = field(default_factory=list[str])
        consecutive_getter_failures_number_to_trigger_warning: list[int] = field(default_factory=lambda: [2, 5, 10])

    pair: list[str] = field(default_factory=list[str])
    url: dict[str, str] = field(default_factory=dict[str, str])
    warning: Warning = field(default_factory=Warning)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    api: APIConfig = field(default_factory=APIConfig)

    # Pre-refresh is performed when Getter is registered, and the results obtained from this refresh will not be pushed.
    # The recommendation is True.
    # When it is False and it has been a long time since the last MessageSynser refresh, it is recommended to manually perform a refresh after MessageSynser is started.
    refresh_when_start: bool = True

    first_get_donot_push: bool = True
    block: list[str] = field(default_factory=list[str])
    perf_merged_details: bool = True
    proxies: dict[str, str] = field(default_factory=dict[str, str])  # This field will be passed directly to requests.request


main_manager = get_config_manager(MainConfig, 'main')
main = main_manager.value
verbose = main.logging.verbose
