"""解析器抽象基类"""

from abc import ABC, abstractmethod
from core.models import ParsedData


class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, filepath: str) -> bool: ...

    @abstractmethod
    def parse(self, filepath: str) -> ParsedData: ...
