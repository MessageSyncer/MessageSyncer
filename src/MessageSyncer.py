import asyncio
import datetime
import os
import sys

import api
import config
import core
import log
import runtime
from model import *


async def main():
    core.main_event_loop = asyncio.get_event_loop()
    core.update_getters()

    await api.serve()


if __name__ == "__main__":
    log.info(f"MessageSyncer ({runtime.version}) started")
    log.info(f"at {Path().absolute()}")
    if runtime.run_in_frozen_mode:
        log.debug(
            f"frozen at {sys._MEIPASS}, build time: {datetime.datetime.fromtimestamp(runtime.build_time)}"
        )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info(f"MessageSyncer exited")
