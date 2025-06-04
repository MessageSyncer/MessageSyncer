from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime

import util


@dataclass
class StructElement(ABC):
    def __str__(self) -> str:
        return ""

    @abstractmethod
    def asmarkdown(self) -> str: ...


@dataclass
class StructText(StructElement):
    text: str
    bold: bool = False
    italic: bool = False

    def __str__(self) -> str:
        return self.text

    def asmarkdown(self) -> str:
        finalstr = ""
        if self.bold:
            finalstr = f"**{finalstr}**"
        if self.italic:
            finalstr = f"*{finalstr}*"
        return self.text.replace("\n", "  \n")


@dataclass
class StructTitle(StructText):
    heading: int = 0

    def __str__(self) -> str:
        return self.text + "\n"

    def asmarkdown(self) -> str:
        finalstr = super().asmarkdown()
        return "#" * self.heading + " " + finalstr + "  \n"


@dataclass
class StructImage(StructElement):
    source: str
    alt: str = ""

    def __str__(self) -> str:
        return "\n"

    def asmarkdown(self, source=None) -> str:
        if source is None:
            source = self.source
        return f"![{self.alt}]({source})  \n"

    @property
    def islocal(self):
        return util.is_local_or_url(self.source) == "local"


@dataclass
class StructURL(StructElement):
    source: str
    title: StructText

    def __str__(self) -> str:
        return self.source

    def asmarkdown(self) -> str:
        return f"[{self.title.asmarkdown()}]({self.source})"


types = {
    "text": StructText,
    "title": StructTitle,
    "image": StructImage,
    "url": StructURL,
}


class Struct:
    def __init__(self, dict_: dict = None) -> None:
        self.content: list[StructElement] = []

        if dict_:
            for element in dict_:
                type_ = element["type"]
                type_ = types[type_]
                data_ = element["data"]
                self.content.append(type_(**data_))

    def image(self, source: str | list[str] = None) -> "Struct":
        return self._create(source, StructImage)

    def text(self, text: str | list[str] = None) -> "Struct":
        return self._create(text, StructText)

    def _create(self, source, type_):
        if isinstance(source, str):
            self.content.append(type_(source))
        elif isinstance(source, list):
            self.content.extend([type_(_source) for _source in source])
        return self

    def extend(self, another: "Struct") -> "Struct":
        for content in another.content:
            self.content.append(content)
        return self

    def asdict(self):
        result = []
        for element in self.content:
            result.append(
                {
                    "type": [k for k, v in types.items() if v == type(element)][0],
                    "data": asdict(element),
                }
            )
        return result

    def __str__(self) -> str:
        return "".join([str(element) for element in self.content])

    def asmarkdown(self) -> str:
        return "".join([element.asmarkdown() for element in self.content])

    def as_preview_str(self):
        selfstripped = str(self).replace("\n", "\\n")
        if len(selfstripped) <= 40:
            return selfstripped
        return selfstripped[:20] + "..." + selfstripped[-20:]

    @staticmethod
    def template1(
        content, ts, title="", url="", username="", images=[], ip="", detail=""
    ) -> "Struct":
        """
        This is the title.

        Content line 1.
        Content line 2.
        Content line n.

        Author · Time · detail1 · detail2 · detailn
        url
        """
        detail_line = "\n"
        time_ = datetime.fromtimestamp(ts).strftime("%H:%M")
        detail_line_first_line_component = [
            c for c in [username, time_, ip, detail] if c != ""
        ]
        detail_line += " · ".join(detail_line_first_line_component)

        if url != "":
            detail_line += "\n" + url

        result = Struct()
        if isinstance(content, Struct):
            if title != "":
                result.text(f"{title}\n\n")
            result.extend(content)
        elif isinstance(content, str):
            if title != "":
                title = title + "\n\n"
            if not content.endswith("\n"):
                content += "\n"
            result.text(f"{title}{content}")
        result.image(images)
        result.text(detail_line)

        return result
