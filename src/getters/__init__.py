import sys
import importlib
from pathlib import Path
from model import *
from util import *

getters_inited: list[Getter] = []
path = Path() / 'getters'


def init_getter(getter_str) -> Getter:
    if matched := [_getter for _getter in getters_inited if _getter.name == getter_str]:
        getter = matched[0]
    else:
        getter = getter_str.split('.')
        getter.append(None)
        getter_type = getter[0]
        getter_detail = getter[1]
        getter = import_all_to_dict(path)[getter_type](getter_detail)
        getters_inited.append(getter)

        logging.debug(f'{getter} initialized')
    return getter
