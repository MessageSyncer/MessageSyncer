from model import *
from util import *
import store
import time
import re
import config
import asyncio
import threading
import aiocron
import network
import warning
import getters
import pushers

setting: dict[Getter, list[str]] = {}


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


def get_adapter(getter=None, pusher=None):
    if getter:
        try:
            getters.get_getter(getter)
        except getters.GetterNotFoundException as e:
            getter_class, _ = getters.parse_getter(getter)
            path = getters.path/getter_class
            clone_from_vcs(config.main.url.get(getter_class, f'https://github.com/MessageSyncer/{getter_class}'), path)
            install_requirements(path)
    if pusher:
        try:
            pushers.get_pusher(pusher)
        except pushers.PusherNotFoundException as e:
            pusher_class, _, _ = pushers.parse_pusher(pusher)
            path = pushers.path/pusher_class
            clone_from_vcs(config.main.url.get(pusher_class, f'https://github.com/MessageSyncer/{pusher_class}'), path)
            install_requirements(path)


async def register_pair(pair_str):
    pair_str: str
    pair_str = pair_str.split(' ', 1)

    get_adapter(pair_str[0], pair_str[1])

    getter = getters.get_getter(pair_str[0])
    push_detail = pair_str[1]

    logging.debug(f'Distribute {push_detail} to {getter}')
    setting.setdefault(getter, []).append(push_detail)

    await register_all_trigger(getter)


async def register_all_trigger(getter: Getter):
    for trigger in getter.config.get('trigger', []):
        register_corn(getter, trigger)
    if config.main.refresh_when_start:
        refresh(getter)
    else:
        getter._first = False


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
        logger.debug(f'Latest list: {list_}')

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
                    for push in setting[getter]:
                        try:
                            await pushers.push_to(push, content)
                        except Exception as e:
                            logger.error(e)
                            await warning.warning(Struct().text(f'Failed to push to {push}: \n{content}'))
                else:
                    logger.debug('Skipped to push because: {}'.format(', '.join(push_passed_reason)))
            except Exception as e:
                logger.error(f'Failed when process_result: {e}', exc_info=True)

        for id_ in list_.copy():
            def pass_(id_):
                if store.Article.get_or_none(store.Article.id == id_):
                    logger.debug(f'{id_} exists. Passed')
                    return True
                logger.info(f'Got new article: {id_}')
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
                    store.Article.from_getresult(_id, detail).save(force_insert=True)
                    for _id in list_
                ]
                await process_result(detail, logging.getLogger(','.join(list_)))
        except NotImplementedError as e:
            works = []

            async def process_signal_article(id):
                detail = await getter.detail(id.replace(getter_prefix, '', 1))
                detail.user_id = getter_prefix + detail.user_id
                store.Article.from_getresult(id, detail).save(force_insert=True)
                await process_result(detail, logging.getLogger(id))
            for id_ in list_:
                works.append(process_signal_article(id_))
            await asyncio.gather(*works)

        logger.debug(f'Refreshing finished')

        getter._number_of_consecutive_failures = 0
        getter._first = False
    except Exception as e:
        logger.error(f'Failed when refreshing: {e}', exc_info=True)

        getter._number_of_consecutive_failures += 1
        if getter._number_of_consecutive_failures in [2, 5, 10]:
            await warning.warning(Struct().text(f'{getter} has failed to update {getter._number_of_consecutive_failures} times in a row.'))

    getter._working = False
    return {}  # TODO: finish it
