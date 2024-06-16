import base64
import json
import yaml
import requests
import logging
import colorlog
import importlib
import sys
import asyncio
from PIL import Image
from pathlib import Path
from peewee import SqliteDatabase
from urllib.parse import urlparse
from unittest.mock import patch


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


def download(url, path):
    path = str(path)
    logging.debug(f'Start to download from {url} to {path}')
    response = requests.get(url)
    if response.status_code == 200:
        with open(path, 'wb') as file:
            file.write(response.content)
        return path
    else:
        raise Exception(f'Download failed: {response.status_code}')


async def async_download(url, path):
    path = str(path)
    logging.debug(f'Start to download from {url} to {path}')
    response = await asyncio.threads.to_thread(requests.get, url, proxies={})
    if response.status_code == 200:
        with open(path, 'wb') as file:
            file.write(response.content)
        return path
    else:
        raise Exception(f'Download failed: {response.status_code}')


def read_file(path):
    with open(str(path), 'r', encoding='utf8') as file:
        return file.read()


def read_json(path):
    return json.loads(read_file(path))


def read_yaml(path):
    return yaml.safe_load(read_file(path))


def write_file(path, content):
    with open(str(path), 'w', encoding='utf8') as file:
        file.write(content)


def write_json(path, content):
    write_file(path, json.dumps(content, ensure_ascii=False))


def write_yaml(path, content):
    write_file(path, yaml.safe_dump(content))


def get_key_by_value(dictionary, value):
    for k, v in dictionary.items():
        if v == value:
            return k


def byte_to_MB(byte):
    return byte / (1024**2)


def _wrap_method(group):
    if group.get('result'):
        return
    result = {}

    wrapper = group['wrapper']
    from_ = group['from']

    for method_name in group['method']:
        absolute_name = from_ + '.' + method_name
        origin_method = eval(absolute_name, group['globals'], {})
        result[method_name] = wrapper(origin_method)

    group['result'] = result


def get_patches(group):
    _wrap_method(group)
    return patch.multiple(group['from'], **group['result'])


def run_with_patch(groups: list[str], func, *args, **kwargs):
    group = groups.pop()
    _wrap_method(group)
    with get_patches(group=group):
        if groups:
            return run_with_patch(groups, func, *args, **kwargs)
        else:
            return func(*args, **kwargs)
