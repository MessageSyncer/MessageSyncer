import base64
import shutil
import json
import yaml
import requests
import logging
import colorlog
import importlib
import subprocess
import sys
import re
import asyncio
from PIL import Image
from pathlib import Path
from peewee import SqliteDatabase
from urllib.parse import urlparse


def generate_function_call(function, *args, **kwargs):
    args_str = ", ".join(repr(arg) for arg in args)
    kwargs_str = ", ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
    all_args_str = ", ".join(filter(None, [args_str, kwargs_str]))
    return f"{function}({all_args_str})"


def try_install_requirements(path: Path):
    # Check if requirements.txt exists
    requirements_file = path / 'requirements.txt'
    if not requirements_file.exists():
        return

    # Use subprocess to call pip to install dependencies
    try:
        subprocess.check_call(['pip', 'install', '-r', str(requirements_file)])
    except subprocess.CalledProcessError as e:
        logging.warning(f"Installation for requirements.txt failed: {e}")


def clone_from_vcs(string: str, path: Path):
    logging.info(f"Cloning {string}...")

    parts = string.split('+', 1)
    if len(parts) == 2:
        vcs = parts[0]
        url = parts[1]
    elif len(parts) == 1:
        vcs = 'git'
        url = parts[0]
    else:
        raise ValueError("Invalid vcs source format")

    target_path = path
    if target_path.exists():
        if target_path.is_dir():
            shutil.rmtree(target_path)

    if vcs == 'git':
        command = ['git', 'clone', url, str(target_path)]
    elif vcs == 'svn':
        command = ['svn', 'checkout', url, str(target_path)]
    elif vcs == 'hg':
        command = ['hg', 'clone', url, str(target_path)]
    elif vcs == 'bzr':
        command = ['bzr', 'branch', url, str(target_path)]
    else:
        raise ValueError(f"Unsupported VCS: {vcs}")

    try:
        subprocess.run(command, check=True)
        logging.info(f"Cloned {vcs} repository from {url} to {target_path}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error cloning repository: {e}")


attr_module = {}


def find_spec_attr(path: Path, name: str) -> object:
    global attr_module

    def process(module, attr):
        attr_module[attr] = module
        return getattr(module, attr)

    if not path.exists():
        raise ValueError(f"The path {path} does not exist.")

    # Convert the path to an absolute path and add it to sys.path
    path = path.resolve()
    sys.path.append(str(path))

    for item in path.glob('*'):
        if item.is_dir() and (item / '__init__.py').exists():
            # Import everything in the package
            try:
                try_install_requirements(item)
                module_name = item.relative_to(path.parent).as_posix().replace('/', '.')
                module = importlib.import_module(module_name)
                # Import everything from the package
                for attr in dir(module):
                    if attr == name:
                        return process(module, attr)
            except Exception as e:
                pass
        elif item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
            # Import everything from a single Python file
            try:
                module_name = item.relative_to(path.parent).with_suffix('').as_posix().replace('/', '.')
                module = importlib.import_module(module_name)
                # Import everything from modules
                for attr in dir(module):
                    if attr == name:
                        return process(module, attr)
            except Exception as e:
                pass
    raise KeyError(name)


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


def is_valid_url(url):
    if url == None:
        return False
    pattern = re.compile(
        r'^(https?|ftp)://'  # http, https
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # 域名
        r'localhost|'  # local host
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IPv4 address
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6 address
        r'(?::\d+)?'  # Port number (optional)
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # Slashes and other characters

    # Use regular expressions to match the given URL
    return re.match(pattern, url) is not None


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
