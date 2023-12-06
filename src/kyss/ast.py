from dataclasses import InitVar, dataclass, field

from .errors import SourceLocation, KyssSchemaError, ordered_set


@dataclass
class Node:
    location: 'SourceLocation' = field(init=False)
    source: InitVar['Source']

    def __post_init__(self, source):
        self.location = SourceLocation.from_source(source)

    def error(self, expected: str) -> KyssSchemaError:
        'Helper function to create an exception from a Node object'
        return KyssSchemaError(self.location, ordered_set(expected))


@dataclass
class StrNode(Node):
    value: str


@dataclass
class ListNode(Node):
    children: list[Node]


@dataclass
class DictNode(Node):
    children: dict[str, Node]
