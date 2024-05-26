from getters import init_getter
from pushers import init_pusher
from model import *
from util import *

import asyncio
import logging
import config
import fresh
import log
import api


async def main():
    matches = fresh.setting
    for pair in config.main.get('pair', []):
        pair: str
        pair = pair.split(' ', 1)

        getter = init_getter(pair[0])
        push_detail = init_pusher(pair[1])

        logging.debug(f'Distribute {push_detail} to {getter}')
        matches.setdefault(getter, []).append(push_detail)

    await fresh.register_all_trigger()

    api.serve()
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    logging.info('Started')
    asyncio.run(main())
