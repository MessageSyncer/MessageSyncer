import sys
import importlib
from pathlib import Path
from model import *
from util import *

getters_inited: list[Getter] = []
path = Path() / 'getters'


class GetterNotFoundException(Exception):
    pass


def parse_getter(getter):
    getter = getter.split('.')
    getter.append(None)
    getter_class = getter[0]
    getter_id = getter[1]
    return getter_class, getter_id


def get_getter(getter_str) -> Getter:
    if matched := [_getter for _getter in getters_inited if _getter.name == getter_str]:
        getter = matched[0]
    else:
        getter_class, getter_id = parse_getter(getter_str)
        try:
            getter = import_all_to_dict(path)[getter_class](getter_id)
        except KeyError:
            raise GetterNotFoundException()
        getters_inited.append(getter)

        logging.debug(f'{getter} initialized')
    return getter
