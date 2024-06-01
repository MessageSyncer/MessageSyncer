from .struct import Struct, StructElement, StructImage, StructText
from .base import Adapter
from .getter_base import GetResult, Getter, GetterConfig, GetterInstanceConfig
from .pusher_base import Pusher, PushResult, PusherConfig, PusherInstanceConfig
import logging
import importlib
import sys
from typing import List
from dataclasses import dataclass, field, asdict
from pathlib import Path

def import_all_to_dict(path: Path) -> dict:
    if not path.exists():
        raise ValueError(f"The path {path} does not exist.")
    
    namespace: dict = {}

    # Convert the path to an absolute path and add it to sys.path
    path = path.resolve()
    sys.path.append(str(path))

    for item in path.rglob('*'):
        if item.is_dir() and (item / '__init__.py').exists():
            # Import everything in the package
            try:
                module_name = item.relative_to(path.parent).as_posix().replace('/', '.')
                module = importlib.import_module(module_name)
                # Import everything from the package
                for attr in dir(module):
                    if not attr.startswith('_'):
                        namespace[attr] = getattr(module, attr)
            except Exception as e:
                pass
        elif item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
            # Import everything from a single Python file
            try:
                module_name = item.relative_to(path.parent).with_suffix('').as_posix().replace('/', '.')
                module = importlib.import_module(module_name)
                # Import everything from modules
                for attr in dir(module):
                    if not attr.startswith('_'):
                        namespace[attr] = getattr(module, attr)
            except Exception as e:
                pass

    return namespace