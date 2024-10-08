from threading import Lock
from util import *
from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, Type
path = Path() / '../data' / 'config'
path.mkdir(parents=True, exist_ok=True)
T = TypeVar('T')
T1 = TypeVar('T1')


class HotReloadConfigManager(Generic[T]):
    def __init__(self, config_path: Path, config_type: T = dict) -> None:
        self.config_type = config_type
        self.config_path = config_path
        self.lock = Lock()

        if not self.config_path.exists():
            self.save(self.config_type())

    @staticmethod
    def allow_dict_access(data_type):
        """
        The shift from using dict as the profile type to using dataclass as the profile type is a disruptive change from Pusher to MessageSyncer.

        To be compatible with all adapters, MessageSyncer supports accessing dataclass instances like accessing dict through the following code.

        This feature will be removed one day in the future. It is not recommended that any adapter developer continue to use dict as a configuration file type. Migrate to dataclass as soon as possible.
        """

        def __getter__(self: object, key, default=None):
            try:
                return self.__getattribute__(key)
            except AttributeError:
                return default

        def get(self, key, default=None):
            return self.__getter__(key, default)

        def __getitem__(self, key):
            return self.__getter__(key)

        data_type.__getter__ = __getter__
        data_type.get = get
        data_type.__getitem__ = __getitem__

    @staticmethod
    def from_dict(data_type: T, data: dict) -> T:
        # TODO: remove dict access support
        """Instantiate data classes from dictionaries, including working with nested data classes."""

        if data_type in [dict, int, str, list, float, None]:
            return data

        try:
            if data_type.__origin__ in [dict, list]:
                return data
        except AttributeError:
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
        return yaml.dump(self.asdict(config), default_flow_style=False, encoding='utf-8', allow_unicode=True).decode('utf-8')

    def save(self, config):
        with self.lock:
            write_file(self.config_path, self.asyaml(config))

    def yaml(self):
        with self.lock:
            if self.config_path.exists():
                config = read_file(self.config_path)
            else:
                self.config_path.touch()
                config = "{}"
            return config

    def dict(self):
        return yaml.load(self.yaml(), Loader=yaml.FullLoader)

    @property
    def value(self) -> T:
        yaml_config = self.yaml()
        dict_config = yaml.safe_load(yaml_config)
        config = HotReloadConfigManager.from_dict(self.config_type, dict_config)
        if self.asyaml(config) != yaml_config:
            self.save(config)
        return config


def get_config_manager(config_type: Type[T] = dict, name='main') -> HotReloadConfigManager[T]:
    config_file = path / f'{name}.yaml'
    return HotReloadConfigManager(config_type=config_type, config_path=config_file)


@dataclass
class MessageSyncerDetail:
    version_commit: str = ''


@dataclass
class MainConfig:
    @dataclass
    class LoggingConfig:
        verbose: bool = False

    @dataclass
    class APIConfig:
        token: list[str] = field(default_factory=list[str])
        port: int = 11589
        cors_allow_origins: list[str] = field(default_factory=lambda: [])

    @dataclass
    class Warning:
        to: list[str] = field(default_factory=list[str])
        consecutive_getter_failures_number_to_trigger_warning: list[int] = field(default_factory=lambda: [2, 5, 10])

    pair: list[str] = field(default_factory=list[str])  # list of pair, partially supports hotreload. Pushers take effect immediately. Getters does not support hotreload.
    url: dict[str, str] = field(default_factory=dict[str, str])  # url of Adapter. Such as `git+https://github.com/user/repo`
    warning: Warning = field(default_factory=Warning)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    api: APIConfig = field(default_factory=APIConfig)

    # Pre-refresh will be executed when Getter is registered if refresh_when_start.
    # The results of each Getter's first refresh will not be pushed if first_get_donot_push.
    # The recommendation is True and True.
    # When refresh_when_start is False and it has been a long time since the last MessageSynser refresh, it is recommended to manually perform a refresh after MessageSynser is started.
    refresh_when_start: bool = True
    first_get_donot_push: bool = True

    block: list[str] = field(default_factory=list[str])
    article_max_ageday: int = 180 # Articles exceeding the number of days corresponding to this number will not be pushed
    perf_merged_details: bool = True
    proxies: dict[str, str] = field(default_factory=dict[str, str])  # This field will be passed directly to requests.request


main_manager = get_config_manager(MainConfig, 'main')


def main():
    return main_manager.value


def messagesyncer_detail() -> MessageSyncerDetail:
    return MessageSyncerDetail(get_current_commit(Path('..')))
