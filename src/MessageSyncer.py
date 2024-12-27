import asyncio
import datetime
import logging

import api
import config
import core
import log
from model import *


async def main():
    core.main_event_loop = asyncio.get_event_loop()
    core.update_getters()

    await api.serve()


if __name__ == "__main__":
    log.init()
    logging.info(f"MessageSyncer ({config.messagesyncer_detail().version}) started")
    logging.info(f"at {Path().absolute()}")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f"MessageSyncer exited")
