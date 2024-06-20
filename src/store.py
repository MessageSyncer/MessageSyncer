from peewee import IntegerField, Model, TextField
from model import *
from util import *

database_path = Path('../data') / 'database'
database_path.mkdir(parents=True, exist_ok=True)
main_db = SqliteDatabase(database_path / 'main.db')


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

    def from_getresult(id: str, getresult: GetResult):
        return Article(id=id, userId=getresult.user_id, ts=getresult.ts, content=getresult.content)


Article.create_table()
pass
