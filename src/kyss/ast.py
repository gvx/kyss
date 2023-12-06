from dataclasses import InitVar, dataclass, field
from typing import ClassVar, Literal

from .errors import KyssSchemaError, SourceLocation, ordered_set


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
class ScalarNode(Node):
    ':class:`Node` subclass that represents scalar values.'

    kind = 'scalar'

    #: A string representing the value of this node.
    value: str

    def require_scalar(self) -> None:
        pass


@dataclass
class SequenceNode(Node):
    ':class:`Node` subclass that represents sequences.'

    kind = 'sequence'

    #: A list of the nodes representing the values of this sequence.
    children: list[Node]

    def require_sequence(self) -> None:
        pass


@dataclass
class MappingNode(Node):
    ':class:`Node` subclass that represents mappings.'

    kind = 'mapping'

    #: A dictionary where the keys are the keys of this mapping (as strings), and the values are the nodes representing the values of this mapping.
    children: dict[str, Node]

    def require_mapping(self) -> None:
        pass
