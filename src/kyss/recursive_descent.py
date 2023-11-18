import re
import sys
from dataclasses import dataclass, replace
from functools import partial
from os import PathLike
from pathlib import Path
from typing import Any, Callable, Protocol, Self, TypeVar, overload, Literal, Never

from .schema import Schema
from .typed_schema import to_schema


@dataclass
class ParsingFailure(Exception):
    '''Raised when trying to parse an invalid kyss file or string.'''

    source: 'Source'
    expected: dict[str, None]

    def format_expected(self) -> str:
        expected = ', '.join(self.expected)
        if len(self.expected) > 1:
            return f'one of {{{expected}}}'
        return expected

    def __str__(self) -> str:
        line_nr, col, line = self.source.get_line_info()
        spaces = ' ' * (col - 1)
        return f'Expected {self.format_expected()}\nLine: {line_nr}\n{line}\n{spaces}^'


def ordered_set(value: str) -> dict[str, None]:
    return {value: None}

_PENDING = object()

@dataclass(frozen=True)
class Source:
    string: str
    index: int = 0
    indentation: tuple[str | Literal[_PENDING], ...] = ('',)

    def advance_to(self, index: int) -> Self:
        return replace(self, index=index)

    def advance(self, count: int) -> Self:
        return self.advance_to(self.index + count)

    def expect(self, expected: str) -> Self:
        if not self.string.startswith(expected, self.index):
            fail(self, repr(expected))
        return self.advance(len(expected))

    def match(self, regex: re.Pattern[str], expected: str | None = None) -> tuple[re.Match[str], Self]:
        match_value = regex.match(self.string, self.index)
        if match_value is None:
            fail(self, expected or str(regex))
        return match_value, self.advance_to(match_value.end())

    def check(self, expected: str) -> bool:
        return self.string.startswith(expected, self.index)

    def indent(self, specific_indentation: str | None = None) -> Self:
        if specific_indentation is not None:
            new_indentation = self.indentation[-1] + specific_indentation
        else:
            new_indentation = _PENDING
        return replace(self, indentation=self.indentation + (new_indentation,))

    def dedent(self) -> Self:
        assert self.indentation
        return replace(self, indentation=self.indentation[:-1])

    def fix_indentation(self, new_indentation: str) -> Self:
        if not new_indentation.startswith(self.indentation[-2]):
            fail(self, 'inconsistent indentation')
        return replace(self, indentation=self.indentation[:-1] + (new_indentation,))

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

type Consumer[T] = Callable[[Source], tuple[T, Source]]

def first_valid[T](source: Source, alternatives: list[Consumer[T]]) -> tuple[T, Source]:
    exp = {}
    for alternative in alternatives:
        try:
            return alternative(source)
        except ParsingFailure as e:
            exp |= e.expected
    raise ParsingFailure(source, exp)


def n_or_more[T](source: Source, repeated: Consumer[T], minimum: int) -> tuple[list[T], Source]:
    parsed = []
    try:
        while True:
            value, source = repeated(source)
            parsed.append(value)
    except ParsingFailure as e:
        expected = e.format_expected()
    if len(parsed) < minimum:
        fail(source, f'At least {minimum} times {expected}')
    return parsed, source


def composed_parsers[T](parsers: list[Consumer[T]], select: int, source: Source) -> tuple[list[T] | T, Source]:
    assert 0 <= select < len(parsers)
    for i, parser in enumerate(parsers):
        parsed_item, source = parser(source)
        if i == select:
            parsed = parsed_item
    return parsed, source


def compose[T](parsers: list[Consumer[T | Any]], *, select: int) -> Consumer[T | list[T]]:
    return partial(composed_parsers, parsers, select)


def fail(s: Source, expectation: str) -> Never:
    raise ParsingFailure(s, ordered_set(expectation))

def expect_regex_factory(regex: str, expectation: str) -> Consumer[str]:
    c = re.compile(regex)
    def f(s: Source) -> tuple[str, Source]:
        match, s = s.match(c, expectation)
        return match.group(), s
    return f

indentation = re.compile(r'[ \t]*')
def expect_indentation(s: Source) -> tuple[None, Source]:
    match, snew = s.match(indentation)
    indentation_found = match.group()
    if s.indentation[-1] is _PENDING:
        return None, snew.fix_indentation(indentation_found)
    if indentation_found == s.indentation[-1]:
        return None, snew
    fail(s, 'more indentation')

plain_re = re.compile(r'(?!-[ \t]|[\'" \t])(:[^ \t\n]|[^ \t\n]#|[^:#\n])+')
def expect_plain_scalar(s: Source) -> tuple[str, Source]:
    # Can't use expect_regex_factory here, because rstrip is needed
    match, s = s.match(plain_re, 'plain scalar')
    return match.group().rstrip(), s

esc_seq_re = re.compile((r"\\(x[a-fA-F0-9]{2}|u[a-fA-F0-9]{4}|U[a-fA-F0-9]{8}|.)"))
SIMPLE: dict[str, str] = {'n': '\n', 't': '\t', 'r': '\r'}
def expect_escape_sequence(s: Source) -> tuple[str, Source]:
    match, snew = s.match(esc_seq_re, 'escape sequence')
    escaped = match.group(1)
    selector = escaped[0]
    if selector in {'\\', '"', "'"}:
        value = selector
    elif selector in SIMPLE:
        value = SIMPLE[selector]
    elif selector in {'x', 'u', 'U'}:
        value = chr(int(escaped[1:], 16))
    else:
        fail(s, 'valid escape sequence')
    return value, snew

expect_double_quoted_contents = expect_regex_factory(r'[^"\n\\]+', 'double quoted string contents')

def expect_double_quoted_scalar(s: Source) -> tuple[str, Source]:
    s = s.expect('"')
    frags = []
    frag: str
    while not s.check('"'):
        frag, s = first_valid(s, [expect_double_quoted_contents, expect_escape_sequence])
        frags.append(frag)
    return ''.join(frags), s.expect('"')

expect_single_quoted_contents = expect_regex_factory(r"[^'\n\\]+", 'single quoted string contents')

def expect_single_quoted_scalar(s: Source) -> tuple[str, Source]:
    s = s.expect("'")
    frags = []
    frag: str
    while not s.check("'"):
        frag, s = first_valid(s, [expect_single_quoted_contents, expect_escape_sequence])
        frags.append(frag)
    return ''.join(frags), s.expect("'")

def expect_scalar(s: Source) -> tuple[str, Source]:
    return first_valid(s, [expect_single_quoted_scalar, expect_double_quoted_scalar, expect_plain_scalar])

def expect_value_scalar(s: Source) -> tuple[str, Source]:
    value, s = expect_value(s)
    _, s = expect_comment(s)
    return value, s

def expect_comment(s: Source, comment: re.Pattern[str] = re.compile(r'(#.*)?')) -> tuple[None, Source]:
    _, s = s.match(comment)
    return None, s

OPT_WHITESPACE = re.compile(r'[ \t]*')
WHITESPACE = re.compile(r'[ \t]+')

def expect_single_newline(s: Source) -> tuple[None, Source]:
    _, s = s.match(OPT_WHITESPACE)
    _, s = expect_comment(s)
    s = s.expect('\n')
    return None, s

def expect_newline(s: Source) -> tuple[None, Source]:
    _, s = n_or_more(s, expect_single_newline, 1)
    return None, s

def expect_sequence_item_sequence(s: Source, indentation: str) -> tuple[list[Any], Source]:
    other_items: list[Any]
    s = s.indent(indentation)
    item, s = expect_sequence_item(s)
    other_items, s = n_or_more(s, compose([expect_newline, expect_indentation, expect_sequence_item], select=2), 0)
    return [item] + other_items, s.dedent()

def expect_sequence_item_mapping(s: Source, indentation: str) -> tuple[dict[str, Any], Source]:
    other_items: list[tuple[str, Any]]
    s = s.indent(indentation)
    (k1, v1), s = expect_mapping_item(s)
    other_items, s = n_or_more(s, compose([expect_newline, expect_indentation, expect_mapping_item], select=2), 0)
    return {k1: v1} | {k: v for k, v in other_items}, s.dedent()

def expect_sequence_item_value(s: Source, indentation: str) -> tuple[Any, Source]:
    return first_valid(s, [partial(expect_sequence_item_sequence, indentation=indentation), partial(expect_sequence_item_mapping, indentation=indentation), expect_value_scalar])

def expect_sequence_item(s: Source) -> tuple[Any, Source]:
    s = s.expect('-')
    ws, s = s.match(WHITESPACE)
    return expect_sequence_item_value(s, ' ' + ws.group())

def expect_sequence(s: Source) -> tuple[list[Any], Source]:
    other_items: list[Any]
    _, s = expect_indentation(s)
    first_item, s = expect_sequence_item(s)
    other_items, s = n_or_more(s, compose([expect_newline, expect_indentation, expect_sequence_item], select=2), 0)
    return [first_item] + other_items, s

def expect_scalar_mapping_value(s: Source) -> tuple[str, Source]:
    _, s = s.match(WHITESPACE)
    return expect_value_scalar(s)

def expect_complex_mapping_value(s: Source) -> tuple[Any, Source]:
    s = s.indent()
    _, s = expect_newline(s)
    value, s = first_valid(s, [expect_sequence, expect_mapping])
    return value, s.dedent()

def expect_mapping_value(s: Source) -> tuple[Any, Source]:
    return first_valid(s, [expect_complex_mapping_value, expect_scalar_mapping_value])

def expect_mapping_item(s: Source) -> tuple[tuple[str, Any], Source]:
    key, s = expect_scalar(s)
    s = s.expect(':')
    value, s = expect_mapping_value(s)
    return (key, value), s

def expect_mapping(s: Source) -> tuple[dict[str, Any], Source]:
    other_items: list[tuple[str, Any]]
    _, s = expect_indentation(s)
    (k1, v1), s = expect_mapping_item(s)
    other_items, s = n_or_more(s, compose([expect_newline, expect_indentation, expect_mapping_item], select=2), 0)
    return {k1: v1} | {k: v for k, v in other_items}, s

def expect_value(s: Source) -> tuple[Any, Source]:
    return first_valid(s, [expect_sequence, expect_mapping, expect_scalar])

def expect_document(s: Source) -> tuple[Any, Source]:
    _, s = n_or_more(s, expect_single_newline, 0)
    value, s = expect_value(s)
    _, s = n_or_more(s, expect_single_newline, 0)
    return value, s


def _parse(s: str) -> Any:
    value, src = expect_document(Source(s))
    if src.index < len(s):
        fail(src, 'end of document')
    return value

def parse_string(s: str, /, schema: Schema | type | None = None) -> Any:
    '''Parse a kyss string. If a Schema or type schema is provided, it will be used to validate the parsed value

    :param s: a str that contains the kyss-encoded value
    :param schema: optional schema to use'''
    value = _parse(s + '\n')
    if schema is None:
        return value
    return to_schema(schema).parse(value)


def parse_file(f: PathLike[str], /, schema: Schema | type | None = None) -> Any:
    '''Parse a kyss file (utf-8 encoded). If a Schema or type schema is provided, it will be used to validate the parsed value

    :param f: a os.PathLike for the file name
    :param schema: optional schema to use'''
    return parse_string(Path(f).read_text(encoding='utf-8'), schema)