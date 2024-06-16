from model import *
from util import *

pushers_inited: list[Pusher] = []
path = Path() / 'pushers'


def get_pusher(pusher) -> tuple[Pusher, dict]:
    _pusher = pusher.rsplit('.', 1)
    pusher = _pusher[0]
    pusher_to = _pusher[1]
    if matched := [_pusher for _pusher in pushers_inited if _pusher.name == pusher]:
        pusher = matched[0]
    else:
        pusher = pusher.split('.')
        pusher = import_all_to_dict(path)[pusher[0]](pusher[1])
        pushers_inited.append(pusher)

        logging.debug(f'{pusher} initialized')

    return pusher, {'to': pusher_to}


async def push_to(pusher, content: Struct):
    pusher, detail = get_pusher(pusher)

    logger = pusher.logger.getChild(f'{hash(content)}')
    logger.debug(f'Start to push {hash(content)}')
    await pusher.push(content, **detail)
    logger.debug('End')
