import util
import requests
import config
import logging
from datetime import datetime


def _process_proxy(dict_: dict):
    dict_.setdefault('proxies', config.main_manager.value.proxies)
    return dict_


def _requests_method_wrapper(origin):
    network_logger = logging.getLogger('requests_proxy')

    def new_method(*args, **kwargs):
        kwargs = _process_proxy(kwargs)
        logger = network_logger.getChild(util.generate_function_call(origin, *args, **kwargs))

        max_retry_time = 2
        for i in range(max_retry_time):
            try:
                start_time = datetime.now()
                logger.debug(f'Trying to request ({i+1}/{max_retry_time})')
                result = origin(*args, **kwargs)
                end_time = datetime.now()
                logger.debug(f'Request finished, cost: {(end_time-start_time).total_seconds()} s')
                return result
            except Exception as e:
                logger.warning(e)
                if i+1 == max_retry_time:
                    raise e
    return new_method


def force_proxies_patch():
    return util.get_patches({
        'from': 'requests.Session',
        'wrapper': _requests_method_wrapper,
        'globals': globals().copy(),
        'method': [
            'get',
            'post',
            'put',
            'delete',
            'head',
            'patch',
            'request',
        ]
    })


def force_proxies(func):
    """This is a decorator that forces all requests from the requests library in the decorated function to use the configured proxy.
    """
    def wrapper(*args, **kwargs):
        result = util.run_with_patch([{
            'from': 'requests.Session',
            'wrapper': _requests_method_wrapper,
            'globals': globals().copy(),
            'method': [
                'get',
                'post',
                'put',
                'delete',
                'head',
                'patch',
                'request',
            ]
        }], func, *args, **kwargs)
        return result
    return wrapper
