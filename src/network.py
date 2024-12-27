import logging
import time
from datetime import datetime
from unittest.mock import patch

import requests

import config
import const
import util


def _process_proxy(dict_: dict):
    dict_.setdefault("proxies", config.main().network.proxies)
    return dict_


original_request_method = requests.Session.request


def requests_proxy(*args, **kwargs):
    kwargs = _process_proxy(kwargs)
    logger = logging.getLogger("requests_proxy")
    total_str = util.generate_function_call_str(
        "requests.Session.request", *args, **kwargs
    )
    request_str = hash(total_str)
    max_retry_time = const.PROXY_REQUEST_MAXRETRYTIME
    for i in range(max_retry_time):
        logger.debug(f"{request_str}: start: {total_str}")
        try:
            retrystr = f"({i+1}/{max_retry_time})"
            logger.debug(f"{request_str}: try{retrystr}")
            start_time = time.time()
            result = original_request_method(*args, **kwargs)
            end_time = time.time()
            logger.debug(f"{request_str}: finished after {end_time-start_time} seconds")
            return result
        except Exception as e:
            logger.warning(f"{request_str}: failed{retrystr}: {e}")
            if i + 1 >= max_retry_time:
                raise e


def force_proxies_patch():
    return patch("requests.Session.request", new=requests_proxy)
