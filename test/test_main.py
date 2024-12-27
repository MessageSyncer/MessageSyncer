import asyncio
import json
import time
from datetime import datetime

import config
import core
import log
import store
from model import *

# log.init()
cur_time = time.time()
test_content_start = Struct.template1(
    content="This is the test content", ts=int(cur_time), title="Test Article"
)
test_content_end = None

last_list = [str(cur_time)]
test_config = config.MainConfig()

test_config.pair = ["TestCaseGetter.1 TestCasePusher.."]
test_config.policy.refresh_when_start = False
test_config.policy.skip_first = False


@dataclass
class TestCaseGetterConfig(GetterConfig):
    trigger: list[str] = field(default_factory=lambda: [])
    getter_config_key: str = "getter_config_value"


@dataclass
class TestCaseGetterInstanceConfig(GetterInstanceConfig):
    getter_config_instance_key: str = "getter_config_instance_value"


class TestCaseGetter(Getter[TestCaseGetterConfig, TestCaseGetterInstanceConfig]):
    def __init__(self, id=None) -> None:
        super().__init__(id)
        self.logger.info(f"{self.name} inited")

    async def list(self) -> list[str]:
        return last_list

    async def detail(self, id: str) -> GetResult:
        return GetResult(
            user_id="TestCase"
            + self.config.getter_config_key
            + self.instance_config.getter_config_instance_key,
            ts=int(cur_time),
            content=test_content_start,
        )


class TestCasePusher(Pusher):
    def __init__(self, id=None) -> None:
        super().__init__(id)

    async def push(self, content: Struct, to: str):
        global test_content_end
        test_content_end = content


async def _refresh():
    core.imported_adapter_classes.add(TestCaseGetter)
    core.imported_adapter_classes.add(TestCasePusher)

    core.init(lambda: test_config)
    core.update_getters()

    await core.refresh_worker(core.registered_getters[0])
    assert str(test_content_end) == str(test_content_start)

    article = store.Article.get_or_none(
        store.Article.id == f"TestCaseGetter_{str(cur_time)}"
    )
    assert article
    assert str(article.content) == str(test_content_start)


def test_refresh():
    asyncio.run(_refresh())
