import asyncio
import dataclasses
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Type, Union
from urllib.parse import urlparse

import git
import requests
from PIL import Image


def generate_function_call_str(function, *args, **kwargs):
    args_str = ", ".join(repr(arg) for arg in args)
    kwargs_str = ", ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
    all_args_str = ", ".join(filter(None, [args_str, kwargs_str]))
    return f"{function}({all_args_str})"


def download(url, path: Path):
    response = requests.get(url, proxies={})
    if response.status_code == 200:
        path.write_bytes(response.content)
    else:
        raise Exception(f"Download failed: {response.status_code}")


async def download_async(url, path: Path):
    await asyncio.threads.to_thread(download, url, path)


def is_valid_url(url):
    if url is None:
        return False
    pattern = re.compile(
        r"^(https?|ftp)://"  # http, https
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # 域名
        r"localhost|"  # local host
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # IPv4 address
        r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"  # IPv6 address
        r"(?::\d+)?"  # Port number (optional)
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )  # Slashes and other characters

    # Use regular expressions to match the given URL
    return re.match(pattern, url) is not None


def byte_to_MB(byte):
    return byte / (1024**2)


def get_git_version(repo_path) -> str:
    """
    Get the version of the current commit. If there's a tag exactly matching
    the current commit, return the tag name. Otherwise, return the short commit hash.

    :param repo_path: Path to the Git repository. Defaults to the current directory.
    :return: Tag name or short commit hash as the version.
    """
    try:
        # Initialize the Git repository object
        repo = git.Repo(repo_path)

        # Get the current commit
        current_commit = repo.head.commit

        # Check for exact matching tag
        tags = [tag.name for tag in repo.tags if tag.commit == current_commit]
        if tags:
            return tags[0]  # Return the first matching tag name

        # Fallback to short commit hash if no matching tag is found
        return current_commit.hexsha[:7]  # Short commit hash (first 7 characters)
    except Exception as e:
        return ""


def get_current_commit(repo_path: Path) -> str:
    """
    Gets the current commit hash value for the specified warehouse.

    :return: The hash value of the current commit
    """
    try:
        repo = git.Repo(str(repo_path))
        return repo.head.commit.hexsha
    except:
        return ""


def dataclass_to_jsonschema(cls: Type) -> Dict[str, Any]:
    if not dataclasses.is_dataclass(cls):
        raise ValueError("Provided class is not a dataclass")

    schema = {"type": "object", "properties": {}, "required": []}

    for field in dataclasses.fields(cls):
        field_schema = {"type": get_json_type(field.type)}
        schema["properties"][field.name] = field_schema
        if field.default is None and field.default_factory is dataclasses.MISSING:
            schema["required"].append(field.name)

    return schema


def get_json_type(field_type: Any) -> str:
    """Map Python types to JSON Schema types."""
    if field_type in {str, int, float, bool}:
        return field_type.__name__
    elif field_type == list or field_type == List:
        return "array"
    elif field_type == dict or field_type == Dict:
        return "object"
    elif dataclasses.is_dataclass(field_type):
        # Nested dataclass
        return dataclass_to_jsonschema(field_type)
    return "string"  # Default to string for unsupported types


def get_nested_value(d: dict, path):
    keys = path.split(".")
    for key in keys:
        d = d[key]
    return d


def remove_nested_key(d: dict, path):
    keys = path.split(".")
    for i, key in enumerate(keys):
        if i == len(keys) - 1:
            try:
                del d[key]
            except:
                pass
        else:
            d = d.setdefault(key, {})


def set_nested_value(d: dict, path, value):
    keys = path.split(".")
    for i, key in enumerate(keys):
        if i == len(keys) - 1:
            d[key] = value
        else:
            d = d.setdefault(key, {})


def is_local_or_url(path_str: str) -> str:
    """
    Determine whether the string is a local path or a web link
    Returns "local" or "url"
    """
    path_str = path_str.strip()

    # Determine whether it is a URL
    parsed = urlparse(path_str)
    if parsed.scheme in ["http", "https"] and parsed.netloc:
        return "url"

    # Determine whether it is a local file path
    path = Path(path_str)
    if path.exists() or path_str.startswith(("/", "./", "../", "~")):
        return "local"

    # A local file that may be a relative path but does not exist is also local
    if not re.match(r"^https?://", path_str):
        return "local"

    # default processing
    return "unknown"


def get_image_mime_suffix(file_path: str) -> str:
    FORMAT_TO_MIME_SUFFIX = {
        "JPEG": "jpeg",
        "PNG": "png",
        "GIF": "gif",
        "BMP": "bmp",
        "TIFF": "tiff",
        "WEBP": "webp",
    }
    try:
        with Image.open(file_path) as img:
            fmt = img.format
            suffix = FORMAT_TO_MIME_SUFFIX.get(fmt.upper())
            if suffix:
                return suffix
            else:
                raise ValueError(f"Unsupported image format: {fmt}")
    except Exception as e:
        raise ValueError(f"Cannot open image file: {e}")
