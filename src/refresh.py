from model import *
from util import *
from store import article_store

import re
import config
import asyncio
import threading
import aiocron
import network

setting: dict[Getter, list[tuple[Pusher, dict]]] = {}


def get_refresh_thread(getter: Getter, var: dict = {}):
    def thread():
        with network.force_proxies_patch():
            var.clear()
            var.update(asyncio.run(_refresh_worker(getter)))
    return threading.Thread(target=thread)


def refresh(getter: Getter):
    get_refresh_thread(getter).start()


async def block_refresh(getter: Getter):
    result = {}
    thread = get_refresh_thread(getter, result)
    thread.start()
    thread.join()
    return result


async def register_all_trigger():
    for getter in setting:
        for trigger in getter.config['trigger']:
            register_corn(getter, trigger)
        if config.main.refresh_when_start:
            refresh(getter)


def register_corn(getter: Getter, trigger: str):
    cron = aiocron.crontab(trigger, refresh, (getter,), start=True)
    getter._trigger[trigger] = cron
    logging.debug(f'{getter} registered: {trigger}')
    return cron


def start_corn(getter: Getter, trigger: str):
    getter._trigger[trigger].start()
    logging.debug(f'{getter} trigger started: {trigger}')


def stop_corn(getter: Getter, trigger: str):
    getter._trigger[trigger].stop()
    logging.debug(f'{getter} trigger stopped: {trigger}')


def unregister_corn(getter: Getter, trigger: str):
    stop_corn(getter, trigger)
    getter._trigger.pop(trigger)
    logging.debug(f'{getter} unregistered: {trigger}')


async def _refresh_worker(getter: Getter):
    global setting

    logger = getter.logger
    getter_type = getter.__class__.__name__
    getter_prefix = getter_type + '_'

    logger.debug('Refreshing')
    if not getter.available:
        logger.debug(f'Unavailable. Passed')
        return {}

    getter._working = True

    try:
        list_ = await getter.list()
        list_ = [getter_prefix + id for id in list_]
        logger.debug(f'-> {list_}')

        async def process_result(result: GetResult, logger: logging.Logger):
            try:
                content = result.content
                content_text = str(content)
                # logger.info(content_text)

                push = True
                push_passed_reason = []

                if getter._first:
                    if config.main.first_get_donot_push:
                        push = False
                        push_passed_reason.append('first_get_donot_push')

                for rule in config.main.block:
                    if re.match(rule, content_text) or re.search(rule, content_text):
                        push = False
                        push_passed_reason.append(f'triggers block "{rule}"')

                if push:
                    for pusher, push_detail in setting[getter]:
                        pushing_logger = logger.getChild(f' -> {pusher} + {push_detail}')
                        pushing_logger.info('Start')
                        push_result = await pusher.push(content, **push_detail)
                        if push_result.succeed:
                            pushing_logger.info('√')
                        else:
                            pushing_logger.warning(f'×: {push_result.exception}')
                else:
                    logger.debug('Skipped to push because: {}'.format(', '.join(push_passed_reason)))
            except Exception as e:
                logger.error(f'× (process_result): {e}', exc_info=True)

        for id_ in list_.copy():
            def pass_(id_):
                if article_store.article_exists(id=id_):
                    logger.debug(f'{id_} exists. Passed')
                    return True
                logger.info(f'+ {id_}')
                return False

            if pass_(id_):
                list_.remove(id_)

        try:
            if not config.main.perf_merged_details:
                raise NotImplementedError()

            if list_:
                detail = await getter.details([id.replace(getter_prefix, '', 1) for id in list_])
                detail.user_id = getter_prefix + detail.user_id
                [
                    article_store.store_article(_id, detail)
                    for _id in list_
                ]
                await process_result(detail, logging.getLogger(','.join(list_)))
        except NotImplementedError as e:
            works = []

            async def process_signal_article(id):
                detail = await getter.detail(id.replace(getter_prefix, '', 1))
                detail.user_id = getter_prefix + detail.user_id
                article_store.store_article(id, detail)
                await process_result(detail, logging.getLogger(id))
            for id_ in list_:
                works.append(process_signal_article(id_))
            await asyncio.gather(*works)

        logger.debug(f'Refreshing finished')
        getter._first = False
    except Exception as e:
        logger.error(f'× (refreshing): {e}', exc_info=True)
    getter._working = False

    return {}  # TODO: finish it
