import base64
import json
import yaml
import requests
import logging
import colorlog
import asyncio
from PIL import Image
from pathlib import Path
from peewee import SqliteDatabase
from urllib.parse import urlparse


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
    response = await asyncio.threads.to_thread(requests.get, url)
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
