import asyncio
import logging
import uvicorn
import log
import config
import refresh
import pushers
import time
import store

from util import *
from model import *
from typing import Annotated, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends, APIRouter, Response, Path, Header, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


HOST = '0.0.0.0'
PORT = config.main().api.port

# Update this field every time when a destructive update is made.
# If a destructive update is made, use this field to control the response model of API.
# [20240702]
VERSION = 20240702

app = FastAPI(title='MessageSyncerAPI', version=str(VERSION))
router = APIRouter(prefix='/api')


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content='Internal server error')


@app.exception_handler(HTTPException)
async def generic_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


def authenticate(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    if not credentials.credentials in config.main().api.token:
        raise HTTPException(403)
    return True


def get_getter(getter_str: str) -> Getter:
    ls = [_getter for _getter in refresh.registered_getters if _getter.name == getter_str]
    if len(ls) != 0:
        return ls[0]
    raise HTTPException(404)


def get_pusher(pusher_str: str) -> Pusher:
    ls = [_pusher for _pusher in pushers.pushers_inited if _pusher.name == pusher_str]
    if len(ls) != 0:
        return ls
    raise HTTPException(404)


@dataclass
class GetterInfo():
    name: str
    class_name: str

    working: bool

    config: dict
    instance_config: dict


@dataclass
class Article():
    id: str
    userId: str
    ts: int
    content: list[dict]


@app.get("/", include_in_schema=False)
async def _():
    return RedirectResponse('./docs')


@router.get("/")
async def hello_world() -> dict:
    return JSONResponse({
        "version": VERSION
    })


@router.post("/pairs/", deprecated=True)
async def create_new_pair(pairs: list[str], auth=Depends(authenticate)):
    _config = config.main()
    _config.pair.extend(pairs)
    config.main_manager.save(_config)
    refresh.update_getters()


@router.post("/pairs/update_getters")
async def update_getters(auth=Depends(authenticate)):
    refresh.update_getters()


@router.post("/adapter_classes/{adapter_class:str}/reload", response_model=type(None))
async def reload_adapter_class(adapter_class: str, auth=Depends(authenticate)):
    try:
        refresh.reload_adapter(adapter_class)
    except refresh.AdapterDoNotExistException():
        raise HTTPException(404)


@router.get("/config/{config_name:str}")
async def get_config(config_name: str, auth=Depends(authenticate)) -> dict:
    return config.get_config_manager(name=config_name).dict()


@router.post("/config/{config_name:str}")
async def update_config(config_name: str, new: dict, auth=Depends(authenticate)):
    config.get_config_manager(name=config_name).save(new)


@router.get("/getters/")
async def list_all_getters(auth=Depends(authenticate)) -> list[GetterInfo]:
    return [
        asdict(GetterInfo(name=getter.name, class_name=getter.class_name, working=getter._working, config=getter.config, instance_config=getter.instance_config))
        for getter in refresh.registered_getters
    ]


@router.post("/getters/refresh", response_model=type(None))
async def refresh_getters(auth=Depends(authenticate)):
    for getter in refresh.registered_getters:
        asyncio.create_task(refresh.refresh(getter))


@router.get("/getters/{getter:str}")
async def getter(getter: str, auth=Depends(authenticate)) -> GetterInfo:
    _getter = get_getter(getter)
    return asdict(GetterInfo(name=_getter.name, class_name=_getter.class_name, working=_getter._working, config=_getter.config, instance_config=_getter.instance_config))


@router.post("/getters/{getter:str}/refresh", response_model=type(None))
async def refresh_getter(getter: str, auth=Depends(authenticate)):
    asyncio.create_task(refresh.refresh(get_getter(getter)))


@router.get("/articles/")
async def list_articles(page: int = 0, page_size: int = 10, auth=Depends(authenticate)) -> list[Article]:
    return [
        Article(ar.id, ar.userId, ar.ts, ar.content.asdict())
        for ar in store.Article.select().order_by(store.Article.ts.desc()).paginate(page, page_size)
    ]


@router.get("/articles/{id}")
async def article(id: str, auth=Depends(authenticate)) -> Article:
    ar = store.Article.get_or_none(store.Article.id == id)
    if ar:
        return Article(id, ar.userId, ar.ts, ar.content.asdict())
    else:
        raise HTTPException(404)


@router.get("/log/")
async def list_log(page: int = 0, page_size: int = 10, auth=Depends(authenticate)) -> list[str]:
    data_list = log.log_list
    start_index = max(0, len(data_list) - (page + 1) * page_size)
    end_index = len(data_list) - page * page_size
    return data_list[start_index:end_index]

app.include_router(router)


async def serve():
    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=PORT, log_level='info', log_config={"version": 1, "disable_existing_loggers": False, "formatters": {}, "handlers": {}, "loggers": {"uvicorn": {"handlers": [], "level": "INFO", "propagate": False}, "uvicorn.error": {"handlers": [], "level": "INFO", "propagate": False}, "uvicorn.access": {"handlers": [], "level": "INFO", "propagate": False}, }, }))

    logging.getLogger('uvicorn').handlers = logging.root.handlers
    logging.getLogger('uvicorn.error').handlers = logging.root.handlers
    logging.getLogger('uvicorn.error').name = 'uvicorn'
    logging.getLogger('uvicorn.access').handlers = logging.root.handlers

    await server.serve()
