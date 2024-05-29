from peewee import CharField, IntegerField, Model
from model import *
from util import *
import config

import json

database_path = Path('../data') / 'database'
database_path.mkdir(parents=True, exist_ok=True)
main_db = SqliteDatabase(database_path / 'main.db')

class _ArticleStore:
    class Article(Model):
        id = CharField(primary_key=True, null=False)
        userId = CharField(null=False)
        ts = IntegerField(null=False)
        content = CharField(null=False)

        class Meta:
            database = main_db

    def __init__(self) -> None:
        _ArticleStore.Article.create_table()

    def store_article(self, id: str, result: GetResult):
        _ArticleStore.Article.create(id=id, userId=result.user_id, ts=result.ts, content=json.dumps(result.content.asdict(), ensure_ascii=False))

    def get_article(self, id: str):
        article = self._get_article_byid(id)
        return GetResult(article.userId, article.ts, Struct(article.content))

    def article_exists(self, id: str) -> bool:
        return self._get_article_byid(id) != None

    def _get_article_byid(self, id: str):
        return _ArticleStore.Article.get_or_none(_ArticleStore.Article.id == id)


article_store = _ArticleStore()
