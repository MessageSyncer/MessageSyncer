from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from datetime import datetime
from util import *


@dataclass
class StructElement(ABC):
    pass


@dataclass
class StructText(StructElement):
    text: str


@dataclass
class StructImage(StructElement):
    source: str
    alt: str = ''


types = {
    'text': StructText,
    'image': StructImage
}


class Struct:
    def __init__(self, dict_: dict = None) -> None:
        self.content: list[StructElement] = []

        if dict_:
            for element in dict_:
                type_ = element['type']
                type_ = types[type_]
                data_ = element['data']
                self.content.append(type_(**data_))

    def image(self, source: str | list[str] = None) -> 'Struct':
        return self._add(source, StructImage)

    def text(self, text: str | list[str] = None) -> 'Struct':
        return self._add(text, StructText)

    def _add(self, source, type_):
        if type(source) == str:
            self.content.append(type_(source))
        elif type(source) == list:
            self.content.extend([type_(_source) for _source in source])
        return self

    def asdict(self):
        result = []
        for element in self.content:
            result.append({
                'type': get_key_by_value(types, type(element)),
                'data': asdict(element)
            })
        return result

    def __str__(self) -> str:
        result = []
        for element in self.content:
            if type(element) == StructText:
                result.append(element.text)
        return '\n'.join(result)

    def asmarkdown(self) -> str:
        result = []
        for element in self.content:
            if type(element) == StructText:
                result.append(element.text)
            if type(element) == StructImage:
                result.append(f'![{element.alt}]({element.source})')
        return '\n'.join(result)

    @staticmethod
    def template1(
        content,
        ts,
        title='',
        url='',
        username='',
        images=[],
        ip='',
        detail=''
    ) -> 'Struct':
        if title != '':
            title = title + '\n\n'
        if ip != '':
            ip = f' · {ip}'
        if detail != '':
            detail = f' · {detail}'
        if username != '':
            username = username + ' · '
        if url != '':
            url = '\n' + url

        result = Struct()
        result.text(f"{title}{content}")
        result.image(images)
        result.text(f"\n\n{username}{datetime.fromtimestamp(ts).strftime('%H:%M')}{ip}{detail}{url}")

        return result
