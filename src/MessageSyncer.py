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
    refresh.update_getters()

    await api.serve()

if __name__ == '__main__':
    logging.info(f'MessageSyncer started at {Path().absolute()}')
    logging.info(f'Commit: {config.messagesyncer_detail().version_commit}')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f'MessageSyncer exited')
