import util
import requests
import config
import logging
from datetime import datetime
from unittest.mock import patch


def _process_proxy(dict_: dict):
    dict_.setdefault('proxies', config.main().proxies)
    return dict_


proxy_logger = logging.getLogger('requests_proxy')
original_request_method = requests.Session.request


def requests_proxy(*args, **kwargs):
    kwargs = _process_proxy(kwargs)
    logger = proxy_logger.getChild(util.generate_function_call('requests.Session.request', *args, **kwargs))
    max_retry_time = 2
    for i in range(max_retry_time):
        try:
            start_time = datetime.now()
            logger.debug(f'Trying to request ({i+1}/{max_retry_time})')
            result = original_request_method(*args, **kwargs)
            end_time = datetime.now()
            logger.debug(f'Request finished, cost: {(end_time-start_time).total_seconds()} s')
            return result
        except Exception as e:
            logger.warning(e)
            if i+1 >= max_retry_time:
                raise e


def force_proxies_patch():
    return patch('requests.Session.request', new=requests_proxy)
