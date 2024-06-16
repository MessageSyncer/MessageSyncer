from pushers import get_pusher, push_to
from model import *

import asyncio

async def main():
    await push_to('EvATive7CloudWarning..',Struct().text('Test'))
asyncio.run(main())