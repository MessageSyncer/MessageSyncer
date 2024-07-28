from model import *
from util import *

pushers_inited: list[Pusher] = []
path = Path() / 'pushers'


class PusherNotFoundException(Exception):
    pass


def parse_pusher(pusher):
    _pusher = pusher.split('.', 2)
    pusher = _pusher[0]
    pusher_id = _pusher[1]
    if pusher_id == '':
        pusher_id = None
    pusher_to = _pusher[2]
    if pusher_to == '':
        pusher_to = None
    return pusher, pusher_id, pusher_to


def _get_pusher(pusher) -> tuple[Pusher, dict]:
    pusher_class, pusher_id, pusher_to = parse_pusher(pusher)
    if matched := [_pusher for _pusher in pushers_inited if _pusher.name == f'{pusher_class}.{pusher_id}']:
        pusher = matched[0]
    else:
        try:
            pusher = find_spec_attr(path, pusher_class)(pusher_id)
        except KeyError:
            raise PusherNotFoundException()
        pushers_inited.append(pusher)

        logging.debug(f'{pusher} initialized')

    return pusher, {'to': pusher_to}


async def push_to(pusher, content: Struct):
    pusher, detail = _get_pusher(pusher)

    logger = pusher.logger.getChild(f'{hash(content)}')
    logger.debug(f'Start to push {hash(content)}')
    await pusher.push(content, **detail)
    logger.debug('End')
