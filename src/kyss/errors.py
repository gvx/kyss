from dataclasses import dataclass

type OrderedSet = dict[str, None]

def ordered_set(value: str) -> OrderedSet:
    return {value: None}

@dataclass(frozen=True)
class SourceLocation:
    string: str
    index: int

    @classmethod
    def from_source(cls, s: 'Source'):
        return cls(s.string, s.index)

    def get_line_info(self) -> tuple[int, int, str]:
        line_nr = self.string.count('\n', 0, self.index)
        if line_nr:
            line_start = self.string.rfind('\n', 0, self.index) + 1
        else:
            line_start = 0
        line_end: int | None = self.string.find('\n', self.index)
        if line_end == -1:
            line_end = None
        column_nr = self.index - line_start
        return line_nr + 1, column_nr, self.string[line_start:line_end]

@dataclass
class KyssError(Exception):
    '''Base class for errors with kyss documents'''

    source: SourceLocation
    expected: OrderedSet

    def format_expected(self) -> str:
        expected = ', '.join(self.expected)
        if len(self.expected) > 1:
            return f'one of {{{expected}}}'
        return expected

    def __str__(self) -> str:
        line_nr, col, line = self.source.get_line_info()
        spaces = ' ' * (col - 1)
        return f'Expected {self.format_expected()} at line {line_nr}:\n{line}\n{spaces}^'

@dataclass
class KyssSyntaxError(KyssError):
    '''Raised when trying to parse an invalid kyss file or string.'''

@dataclass
class KyssSchemaError(KyssError):
    '''Raised when a kyss value is able to be parsed but is not accepted by the given schema.'''
