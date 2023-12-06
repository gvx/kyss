from typing import Literal, ClassVar
from dataclasses import InitVar, dataclass, field

from .errors import SourceLocation, KyssSchemaError, ordered_set


@dataclass
class Node:
    'Represents the raw, parsed but as of yet unvalidated data.'

    location: 'SourceLocation' = field(init=False)
    source: InitVar['Source']

    #: Which kind of value this node represents.
    kind: ClassVar[Literal['mapping', 'sequence', 'scalar']]

    def __post_init__(self, source):
        self.location = SourceLocation.from_source(source)

    def error(self, expected: str) -> KyssSchemaError:
        'Helper function to create an exception from a Node object'
        return KyssSchemaError(self.location, ordered_set(expected))

    def is_mapping(self) -> bool:
        '''Returns ``True`` for nodes that represent mappings.'''
        return False

    def is_sequence(self) -> bool:
        '''Returns ``True`` for nodes that represent sequences.'''
        return False

    def is_scalar(self) -> bool:
        '''Returns ``True`` for nodes that represent scalar values.'''
        return False

    def require_mapping(self) -> None:
        '''Convenience function that raises :exc:`KyssSchemaError` for nodes that do not represent mappings.'''
        raise self.error('mapping')

    def require_sequence(self) -> None:
        '''Convenience function that raises :exc:`KyssSchemaError` for nodes that do not represent sequences.'''
        raise self.error('sequence')

    def require_scalar(self) -> None:
        '''Convenience function that raises :exc:`KyssSchemaError` for nodes that do not represent scalar values.'''
        raise self.error('scalar')


@dataclass
class StrNode(Node):
    ':class:`Node` subclass that represents scalar values.'

    kind = 'scalar'

    #: A string representing the value of this node.
    value: str

    def is_scalar(self) -> bool:
        return True

    def require_scalar(self) -> None:
        pass


@dataclass
class ListNode(Node):
    ':class:`Node` subclass that represents sequences.'

    kind = 'sequence'

    #: A list of the nodes representing the values of this sequence.
    children: list[Node]

    def is_sequence(self) -> bool:
        return True

    def require_sequence(self) -> None:
        pass


@dataclass
class DictNode(Node):
    ':class:`Node` subclass that represents mappings.'

    kind = 'mapping'

    #: A dictionary where the keys are the keys of this mapping (as strings), and the values are the nodes representing the values of this mapping.
    children: dict[str, Node]

    def is_mapping(self) -> bool:
        return True

    def require_mapping(self) -> None:
        pass
