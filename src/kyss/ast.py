from dataclasses import dataclass, field, InitVar

from .errors import SourceLocation

@dataclass
class Node:
    location: 'SourceLocation' = field(init=False)
    source: InitVar['Source']

    def __post_init__(self, source):
        self.location = SourceLocation.from_source(source)


@dataclass
class StrNode(Node):
    value: str


@dataclass
class ListNode(Node):
    children: list[Node]


@dataclass
class DictNode(Node):
    children: dict[str, Node]
