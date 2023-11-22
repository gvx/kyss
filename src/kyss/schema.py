from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from decimal import Decimal as PyDecimal
from decimal import InvalidOperation
from typing import (Any, NotRequired, Required, Self, get_args, get_origin,
                    is_typeddict)

#: Passed into :meth:`Schema.parse`
type RawParsed = str | dict[str, RawParsed] | list[RawParsed]

class SchemaError(Exception):
    '''Raised when a kyss value is able to be parsed but is not accepted by the given schema.'''
    def __init__(self, expected: str, found: RawParsed) -> None:
        self.expected = expected
        self.found = found
    def __str__(self) -> str:
        return f'expected {self.expected}, found {self.found!r}'

class Schema:
    '''Base class for all schema builders. You can implement your own schema builder by subclassing ``Schema`` and overriding the ``parse`` method.'''

    def parse(self, v: RawParsed) -> Any:
        '''Validates its argument. If the argument is accepted, returns either the argument unchanged or a value to replace it.
        If the argument is not accepted, raises :py:class:`SchemaError`.'''

        raise NotImplementedError

    def __or__(self, other: 'Schema') -> 'Alternatives':
        return Alternatives([*self._get_alternatives(), *other._get_alternatives()])

    def _get_alternatives(self) -> Iterator['Schema']:
        yield self

    def wrap_in(self, fn: Callable[[Any], Any]) -> 'Wrapper':
        r'''Wrap a schema in a callable.

        >>> parse_string('6', Int().wrap_in(lambda x: x * 7))
        42
        >>> parse_string('- one\n- seven\n- thirteen', Sequence(Str().wrap_in(len)))
        [3, 5, 8]
        '''

        return Wrapper(self, fn)

@dataclass
class Wrapper(Schema):
    schema: Schema
    fn: Callable[[Any], Any]

    def parse(self, v: RawParsed) -> Any:
        return self.fn(self.schema.parse(v))

@dataclass
class Alternatives(Schema):
    '''``schema_1 | schema_2 | ... | schema_n`` <=> ``Alternatives([schema_1, schema_2, ..., schema_n])``

    This tries to validate the parsed value with each schema given. The first schema that accepts the value is used.
    Only fails if none of the alternatives accept it.'''

    alternatives: list[Schema]

    def parse(self, v: RawParsed) -> Any:
        errs: list[SchemaError | ExceptionGroup[SchemaError]] = []
        for alternative in self.alternatives:
            try:
                return alternative.parse(v)
            except* SchemaError as e:
                errs.extend(e.exceptions)
        raise ExceptionGroup('none of alternatives valid', errs)

    def _get_alternatives(self) -> Iterator[Schema]:
        yield from self.alternatives

@dataclass
class Str(Schema):
    'Accepts any scalar and produces it unchanged.'

    def parse(self, v: RawParsed) -> Any:
        if not isinstance(v, str):
            raise SchemaError('string', v)
        return v

@dataclass
class Bool(Schema):
    "Accepts scalars that case-insensitively equal to 'true' or 'false'. Produces a ``bool``."
    def parse(self, v: RawParsed) -> Any:
        if isinstance(v, str):
            v = v.lower()
            if v == 'true':
                return True
            elif v == 'false':
                return False
        raise SchemaError('true or false', v)

@dataclass
class Int(Schema):
    'Accepts scalars that Python can interpret as integers. Produces an ``int``.'
    def parse(self, v: RawParsed) -> Any:
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                pass
        raise SchemaError('integer', v)

@dataclass
class Float(Schema):
    'Accepts scalars that Python can interpret as floating point numbers. Produces a ``float``.'
    def parse(self, v: RawParsed) -> Any:
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                pass
        raise SchemaError('floating point number', v)


@dataclass
class Decimal(Schema):
    'Accepts scalars that Python can interpret as a decimal number. Produces a ``decimal.Decimal``.'
    def parse(self, v: RawParsed) -> Any:
        if isinstance(v, str):
            try:
                return PyDecimal(v)
            except InvalidOperation:
                pass
        raise SchemaError('decimal number', v)

@dataclass
class Sequence(Schema):
    'Accepts sequences where each item is accepted by the ``item`` schema. Produces a ``list``.'

    item: Schema

    def parse(self, v: RawParsed) -> Any:
        if not isinstance(v, list):
            raise SchemaError('sequence', v)
        return [self.item.parse(item) for item in v]

@dataclass
class Mapping(Schema):
    '''Accepts mappings. Produces a ``dict``.

    :param required: maps required keys to the schemas for their respective values.
    :param values: the schema used for values whose keys are not specified in either required or optional. If ``None``, rejects mappings with unspecified keys.
    :param optional: maps optional keys to the schemas for their respective values.'''

    required: dict[str, Schema]
    values: Schema | None = None
    optional: dict[str, Schema] | None = field(default=None, kw_only=True)

    def parse(self, v: RawParsed) -> Any:
        if not isinstance(v, dict):
            raise SchemaError('mapping', v)
        if missing_keys := self.required.keys() - v.keys():
            raise SchemaError(f'a mapping that has the keys {sorted(self.required)}', v)
        unspecified_keys = v.keys() - self.required.keys()
        if self.optional is not None:
            unspecified_keys -= self.optional.keys()
        if unspecified_keys and self.values is None:
            keys = sorted([*self.required, *(self.optional or ())])
            raise SchemaError(f'a mapping that only has the keys {keys}', v)
        specified = {key: schema.parse(v[key]) for key, schema in self.required.items()}
        if self.optional is not None:
            specified |= {key: schema.parse(v[key]) for key, schema in self.optional.items() if key in v}
        if unspecified_keys and self.values is not None:
            return specified | {key: self.values.parse(v[key]) for key in unspecified_keys}
        return specified

@dataclass
class SequenceOrSingle(Schema):
    '''Accepts either a sequence where each item is accepted by ``item`` or a non-sequence value that is accepted by ``item``. Always produces a ``list``, regardless.

    :param item: the schema used for either the sequence items or the non-sequence value.'''

    item: Schema

    def parse(self, v: RawParsed) -> Any:
        if isinstance(v, list):
            return [self.item.parse(item) for item in v]
        return [self.item.parse(v)]

@dataclass
class CommaSeparated(Schema):
    '''Accepts a scalar, splits it on commas. Produces a ``list``.

    :param item: schema that should accept a scalar for the substrings.
    '''

    item: Schema

    def parse(self, v: RawParsed) -> Any:
        if not isinstance(v, str):
            raise SchemaError('string', v)
        return [self.item.parse(item) for item in v.split(',')]

@dataclass
class Passthrough(Schema):
    '''Accepts any value and produces it unchanged.'''

    def parse(self, v: RawParsed) -> Any:
        return v
