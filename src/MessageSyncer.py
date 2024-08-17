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
import importing


async def main():
    refresh.main_event_loop = asyncio.get_event_loop()
    importing.import_all([pushers.path, getters.path])
    refresh.update_getters()

    await api.serve()

if __name__ == '__main__':
    logging.info(f'MessageSyncer started at {Path().absolute()}')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f'MessageSyncer exited')
