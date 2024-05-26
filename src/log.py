import logging
import colorlog
from util import *

path = Path() / '../data' / 'log'
path.mkdir(parents=True, exist_ok=True)


def get_logging_handlers(log_name):
    import config
    file_level = console_level = logging.DEBUG if config.verbose else logging.INFO
    log_file = path / f'{log_name}.log'
    format = '%(asctime)s[%(levelname)s][%(name)s] %(message)s'

    if not log_file.exists():
        log_file.parent.mkdir(exist_ok=True)
        log_file.touch()

    try:
        adjust_log_file(log_file)
    except:
        pass

    file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(logging.Formatter(format))

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

    return [file_handler, console_handler]


def adjust_log_file(log_file):
    log_backup_file = Path(str(log_file) + '.bak')
    if log_file.exists():
        if byte_to_MB(log_file.stat().st_size) > 200:
            if log_backup_file.exists():
                log_backup_file.unlink()
            log_file.rename(log_backup_file)


[logging.getLogger(name).setLevel(logging.INFO) for name in ('peewee', 'asyncio', 'tzlocal', 'PIL.Image')]
logging.basicConfig(level=logging.DEBUG, handlers=get_logging_handlers('root'))

root = logging.root
