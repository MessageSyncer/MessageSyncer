import datetime
import json
from datetime import datetime
from typing import Dict, Optional

import requests
from peewee import (
    AutoField,
    CharField,
    DateTimeField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)

from model import *

database_path = Path("data") / "database"
database_path.mkdir(parents=True, exist_ok=True)
storage_path = Path("data") / "storage"
storage_path.mkdir(parents=True, exist_ok=True)
main_db = SqliteDatabase(database_path / "main.db")


class StructField(TextField):
    def db_value(self, value: Struct):
        return json.dumps(value.asdict(), ensure_ascii=False)

    def python_value(self, value):
        return Struct(dict_=json.loads(value))


class Article(Model):
    id = TextField(primary_key=True, null=False)
    userId = TextField(null=False)
    ts = IntegerField(null=False)
    content = StructField(null=False)

    class Meta:
        database = main_db

    @classmethod
    def from_getresult(cls, id: str, getresult: GetResult) -> "Article":
        return cls(
            id=id, userId=getresult.user_id, ts=getresult.ts, content=getresult.content
        )


Article.create_table()
