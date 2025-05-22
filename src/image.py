import asyncio
import base64
import random
import string
from hashlib import sha256
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from PIL import Image

import store
import util
from model.struct import StructImage

path = Path() / "data" / "pic"
path.mkdir(parents=True, exist_ok=True)


async def download_list(
    ls: list[str], after_download_hook: Callable[[str, str, bool], str] = None
) -> list[str]:
    pics = {p: None for p in ls}
    works = []

    async def process_picture(picurl):
        try:
            path, downloaded = await download_withcache(picurl)
            if after_download_hook:
                path = await asyncio.threads.to_thread(
                    after_download_hook, *(picurl, path, downloaded)
                )
            pics[picurl] = path
        except:
            pics.pop(picurl)

    for pic in ls:
        works.append(process_picture(pic))

    await asyncio.gather(*works)
    return [str(pic) for pic in pics.values()]


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_data = base64.b64encode(image_data).decode("utf-8")
        return base64_data


def webp2png(path: Path):
    # starttime = time.time()
    temp_path = Path(path.parent / "_webp2png_temp_" + path.name)
    webp = Image.open(path)
    webp.save(temp_path, "png", save_all=True, optimize=True)
    try:
        path.unlink(True)
        temp_path.rename(path)
        return path
    except Exception as e:
        return temp_path


async def download_withcache(url) -> tuple[str, bool]:
    global path
    if not util.is_valid_url(url):
        raise Exception("Pic url not valid")
    prased_url = urlparse(url)
    filename: str = prased_url.path.split("/")[-1]

    _path = path / filename
    if not _path.exists():
        await util.download_async(url, _path)
        return _path.absolute(), True
    else:
        return _path.absolute(), False


def get_public_url(img: StructImage, messagesyncer_base_url: str) -> str:
    if img.islocal:
        id_ = ""
        path = Path(img.source)
        filename = path.name

        if query_res := store.ImageStorage.get_or_none(
            store.ImageStorage.filename == filename
        ):
            id_ = query_res.id
        else:
            hash_src = filename + "".join(
                random.choices(string.ascii_letters + string.digits, k=8)
            )
            id_ = sha256(hash_src.encode()).hexdigest().lower()[0:32]
            mime = util.get_image_mime_suffix(str(path.absolute()))
            store.ImageStorage.create(filename=filename, id=id_, mime=mime)
        return f"{messagesyncer_base_url}/res/img/{id_}"
    else:
        return img.source
