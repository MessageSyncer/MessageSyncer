import config
from model import *
from pushers import push_to


async def warning(content: Struct):
    try:
        pushto = config.main().warning.to
        for pusher in pushto:
            await push_to(pusher, content)
    except Exception as e:
        logging.fatal(f'Failure to issue alarm: {e}', exc_info=True)
