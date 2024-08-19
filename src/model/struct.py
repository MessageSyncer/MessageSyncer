from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from datetime import datetime
from util import *


@dataclass
class StructElement(ABC):
    def __str__(self) -> str:
        return ''

    @abstractmethod
    def asmarkdown(self) -> str:
        pass


@dataclass
class StructText(StructElement):
    text: str

    def __str__(self) -> str:
        return self.text

    def asmarkdown(self) -> str:
        return self.text


@dataclass
class StructImage(StructElement):
    source: str
    alt: str = ''

    def __str__(self) -> str:
        return '\n'

    def asmarkdown(self) -> str:
        return f'![{self.alt}]({self.source})\n'


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
        return self._create(source, StructImage)

    def text(self, text: str | list[str] = None) -> 'Struct':
        return self._create(text, StructText)

    def _create(self, source, type_):
        if type(source) == str:
            self.content.append(type_(source))
        elif type(source) == list:
            self.content.extend([type_(_source) for _source in source])
        return self

    def extend(self, another: 'Struct') -> 'Struct':
        for content in another.content:
            self.content.append(content)
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
        return '\n'.join([str(element) for element in self.content])

    def asmarkdown(self) -> str:
        return '\n'.join([element.asmarkdown() for element in self.content])

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
        if ip != '':
            ip = f' · {ip}'
        if detail != '':
            detail = f' · {detail}'
        if username != '':
            username = username + ' · '
        if url != '':
            url = '\n' + url

        result = Struct()
        if type(content) == Struct:
            if title != '':
                title = title + '\n'
                result.text(f"{title}")
            result.extend(content)
        else:
            if title != '':
                title = title + '\n\n'
            result.text(f"{title}{content}")
        result.image(images)
        result.text(f"\n{username}{datetime.fromtimestamp(ts).strftime('%H:%M')}{ip}{detail}{url}")

        return result
