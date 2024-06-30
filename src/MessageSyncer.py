from model import *
from util import *

import asyncio
import logging
import config
import refresh
import log
import api
import getters
import pushers


def get_adapter(getter=None, pusher=None):
    if getter:
        try:
            getters.get_getter(getter)
        except getters.GetterNotFoundException as e:
            getter_class, _ = getters.parse_getter(getter)
            clone_from_vcs(config.main.url.get(getter_class, f'https://github.com/MessageSyncer/{getter_class}'), getters.path, getter_class)
    if pusher:
        try:
            pushers.get_pusher(pusher)
        except pushers.PusherNotFoundException as e:
            pusher_class, _, _ = pushers.parse_pusher(pusher)
            clone_from_vcs(config.main.url.get(pusher_class, f'https://github.com/MessageSyncer/{pusher_class}'), pushers.path, pusher_class)


async def main():
    matches = refresh.setting
    for pair in config.main.pair:
        pair: str
        pair = pair.split(' ', 1)

        get_adapter(pair[0], pair[1])

        getter = getters.get_getter(pair[0])
        push_detail = pair[1]

        logging.debug(f'Distribute {push_detail} to {getter}')
        matches.setdefault(getter, []).append(push_detail)

    await refresh.register_all_trigger()

    api.serve()
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    logging.info('Started')
    asyncio.run(main())
