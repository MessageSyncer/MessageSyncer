import util
import requests
import config


def _process_proxy(dict_: dict):
    dict_.setdefault('proxies', config.main.proxies)
    return dict_


def _requests_method_wrapper(origin):
    def new_method(*args, **kwargs):
        kwargs = _process_proxy(kwargs)

        max_retry_time = 2
        for i in range(max_retry_time):
            try:
                return origin(*args, **kwargs)
            except:
                if i == max_retry_time-1:
                    raise
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
