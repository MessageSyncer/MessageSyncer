from getters import get_getter
from pushers import get_pusher
from model import *
from util import *

import asyncio
import logging
import config
import refresh
import log
import api


async def main():
    matches = refresh.setting
    for pair in config.main.pair:
        pair: str
        pair = pair.split(' ', 1)

        getter = get_getter(pair[0])
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
