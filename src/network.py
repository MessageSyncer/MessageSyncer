import util
import requests
import config


def _process_proxy(dict_: dict):
    dict_.setdefault('proxies', config.main.proxies)
    return dict_


def _requests_method_wrapper(origin):
    def new_method(*args, **kwargs):
        kwargs = _process_proxy(kwargs)
        return origin(*args, **kwargs)
    return new_method


force_proxies_patch = util.get_patches({
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
    """This is a decorator, and the decorated function will enforce the use of the configured proxy.
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
