"""解析器注册中心"""

from .base import BaseParser
from .metv6 import METV6Parser


class ParserRegistry:
    _parsers: list[BaseParser] = [METV6Parser()]

    @classmethod
    def register(cls, parser: BaseParser):
        cls._parsers.append(parser)

    @classmethod
    def get_parser(cls, filepath: str) -> BaseParser | None:
        for parser in cls._parsers:
            if parser.can_parse(filepath):
                return parser
        return None
