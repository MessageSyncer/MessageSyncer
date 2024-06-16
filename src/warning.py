import config
from model import *
from pushers import get_pusher, push_to


async def warning(content: Struct):
    try:
        pushto = config.main_manager.value.warning.to
        for pusher in pushto:
            await push_to(pusher, content)
    except Exception as e:
        logging.fatal(f'Failure to issue alarm: {e}', exc_info=True)
