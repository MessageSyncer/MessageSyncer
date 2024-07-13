from model import *
from util import *

import asyncio
import logging
import config
import refresh
import log
import api


async def main():
    refresh.main_event_loop = asyncio.get_event_loop()
    for pair in config.main.pair:
        await refresh.register_pair(pair)

    api.serve()
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    logging.info('MessageSyncer started')
    asyncio.run(main())
