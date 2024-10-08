from model import *
from util import *
from concurrent.futures import ThreadPoolExecutor
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
import importing
import concurrent
import util

registered_getters: list[Getter] = []
main_event_loop = None


class AdapterDoNotExistException(Exception):
    pass


def register_getter(getter: Getter):
    refresh_trigger(getter)
    if config.main().refresh_when_start:
        asyncio.create_task(refresh(getter))
    registered_getters.append(getter)
    logging.debug(f'Getter registered: {getter}')


def unregister_getter(getter: Getter):
    for trigger in list(getter._triggers.keys()):
        unregister_corn(getter, trigger)
    registered_getters.remove(getter)
    logging.debug(f'Getter unregistered: {getter}')


def refresh_trigger(getter: Getter):
    triggers = getter.config.get('trigger', [])
    override_triggers = getter.instance_config.get('override_trigger', None)
    if override_triggers != None:
        triggers = override_triggers

    for trigger in list(getter._triggers.keys()):
        if not trigger in triggers:
            unregister_corn(getter, trigger)

    for trigger in triggers:
        if not trigger in list(getter._triggers.keys()):
            register_corn(getter, trigger)


def register_corn(getter: Getter, trigger: str):
    cron = aiocron.crontab(trigger, refresh, (getter,), start=True, loop=main_event_loop)
    getter._triggers[trigger] = cron
    getter.logger.debug(f'Trigger registered: {trigger}')
    return cron


def unregister_corn(getter: Getter, trigger: str):
    stop_corn(getter, trigger)
    getter._triggers.pop(trigger)
    getter.logger.debug(f'Trigger unregistered: {trigger}')


def start_corn(getter: Getter, trigger: str):
    getter._triggers[trigger].start()
    getter.logger.debug(f'Trigger started: {trigger}')


def stop_corn(getter: Getter, trigger: str):
    getter._triggers[trigger].stop()
    getter.logger.debug(f'Trigger stopped: {trigger}')


def reload_adapter(name: str):
    try:
        parent_classes = importing.details[name].obj.__bases__
    except:
        raise AdapterDoNotExistException()
    if not importing.details[name].reload():
        importing.import_all([getters.path, pushers.path])
    new_adapter_class = importing.details[name].obj

    if Getter in parent_classes:
        for getter in registered_getters.copy():
            if getter.class_name == name:
                unregister_getter(getter)
        update_getters()


def install_adapter(name: str, type_: type):
    if type_ == Getter:
        path = getters.path/name
    elif type_ == Pusher:
        path = pushers.path/name
    logging.debug(f'Start to install {name}')
    clone_from_vcs(
        config.main().url.get(name, f'https://github.com/MessageSyncer/{name}'),
        path)
    importing.import_all([path/'..'])
    return importing.details[name].obj


def get_adapter_class(adapter_class_name, type_: type):
    # logging.debug(f'Seeking adapter_class {adapter_class_name}')
    try:
        return importing.details[adapter_class_name].obj
    except KeyError:
        try:
            importing.import_all([getters.path, pushers.path])
            return importing.details[adapter_class_name].obj
        except KeyError:
            try:
                return install_adapter(adapter_class_name, type_)
            except:
                raise Exception(f'Cannot find adapter_class {adapter_class_name}')


def parse_pairs():
    result: dict[Getter, list[str]] = {}
    for pair_str in config.main().pair:
        try:
            pair_str: str
            getter_str, pusher_str = pair_str.split(' ', 1)
            getter_class_name, getter_id = getters.parse_getter(getter_str)
            pusher_class_name, _, _ = pushers.parse_pusher(pusher_str)
            getter_class = get_adapter_class(getter_class_name, Getter)
            pusher_class = get_adapter_class(pusher_class_name, Pusher)
        except Exception as e:
            logging.warning(f'Failed to parse {pair_str} beacuse {e}. Skipped')
            continue

        if (matched := [_getter for _getter in registered_getters if _getter.name == getter_str]):
            getter = matched[0]
        elif (matched := [_getter for _getter in result if _getter.name == getter_str]):
            getter = matched[0]
        else:
            getter = getter_class(getter_id)
            logging.debug(f'{getter} initialized')

        result.setdefault(getter, []).append(pusher_str)
    return result


def update_getters():
    pairs_details = parse_pairs()
    removed = []
    added = []
    for getter in registered_getters:
        if not getter in pairs_details:
            unregister_getter(getter)
            removed.append(getter)
    for getter in pairs_details:
        if not getter in registered_getters:
            register_getter(getter)
            added.append(getter)

@dataclass
class RefreshResultSingle(GetResult):
    content: list[dict]


RefreshResult = list[RefreshResultSingle]


async def refresh(getter: Getter) -> RefreshResult:
    refresh_trigger(getter)

    async def thread_worker():
        with network.force_proxies_patch():
            result_data = await _refresh_worker(getter)
            return result_data

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, lambda: asyncio.run(thread_worker()))
    return result


async def _refresh_worker(getter: Getter) -> RefreshResult:
    logger = getter.logger
    getter_type = getter.__class__.__name__
    getter_prefix = getter_type + '_'

    logger.debug('Refreshing')
    if not getter.available:
        logger.debug(f'Unavailable. Skipped')
        return []

    getter._working = True

    new_articles_during_fresh = []
    try:
        list_ = await getter.list()
        list_ = [getter_prefix + id for id in list_]
        logger.debug(f'Latest list: {list_}')

        async def process_result(result: GetResult, logger: logging.Logger):
            try:
                new_articles_during_fresh.append(RefreshResultSingle(result.user_id, result.ts, result.content.asdict()))
                content = result.content
                content_text = str(content)
                # logger.info(content_text)

                push = True
                push_passed_reason = []

                if getter._first:
                    if config.main().first_get_donot_push:
                        push = False
                        push_passed_reason.append('first_get_donot_push')

                for rule in config.main().block:
                    if re.match(rule, content_text) or re.search(rule, content_text):
                        push = False
                        push_passed_reason.append(f'triggers block "{rule}"')

                if (time.time() - result.ts)/3600/24 > config.main().article_max_ageday:
                    push = False
                    push_passed_reason.append('exceed article_max_ageday')

                if push:
                    for push_detail in parse_pairs()[getter]:
                        try:
                            await pushers.push_to(push_detail, content)
                        except Exception as e:
                            logger.error(e)
                            await warning.warning(Struct().text(f'Failed to push to {push_detail}: \n{content}'))
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
            if not config.main().perf_merged_details:
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
        if getter._number_of_consecutive_failures in config.main().warning.consecutive_getter_failures_number_to_trigger_warning:
            await warning.warning(Struct().text(f'{getter} has failed to update {getter._number_of_consecutive_failures} times in a row.'))

    getter._working = False
    return new_articles_during_fresh
