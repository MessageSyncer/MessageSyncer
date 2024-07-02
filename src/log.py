import logging
import colorlog
from datetime import datetime
from util import *

path = Path() / '../data' / 'log'
path.mkdir(parents=True, exist_ok=True)

log_list: list[str] = []


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        log_entry = self.format(record)
        log_list.append(log_entry)


def get_logging_handlers(log_name):
    import config
    list_level = file_level = console_level = logging.DEBUG if config.verbose else logging.INFO
    log_file = path / f'{log_name}-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.log'
    format = '%(asctime)s[%(levelname)s][%(name)s] %(message)s'

    if not log_file.exists():
        log_file.parent.mkdir(exist_ok=True)
        log_file.touch()

    file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(logging.Formatter(format))

    list_handler = ListHandler()
    list_handler.setLevel(list_level)
    list_handler.setFormatter(logging.Formatter(format))

    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(colorlog.ColoredFormatter(
        f'%(log_color)s{format}',
        log_colors={
            'DEBUG': 'reset',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))

    return [file_handler, console_handler, list_handler]


# [logging.getLogger(name).setLevel(logging.INFO) for name in ('peewee', 'asyncio', 'tzlocal', 'PIL.Image')]
logging.basicConfig(level=logging.DEBUG, handlers=get_logging_handlers('root'))
