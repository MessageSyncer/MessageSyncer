import sys
import importlib
from pathlib import Path
from model import *
from util import *

getters_inited: list[Getter] = []
path = Path() / 'getters'


def parse_getter(getter):
    getter = getter.split('.')
    getter.append(None)
    getter_class = getter[0]
    getter_id = getter[1]
    return getter_class, getter_id
