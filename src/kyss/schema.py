from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from decimal import Decimal as PyDecimal
from typing import (Any, NotRequired, Required, Self, get_args,
                    get_origin, is_typeddict)

type RawParsed = str | dict[str, Any] | list[Any]  # Where issubclass(Any, RawParsed)

class SchemaError(Exception):
    def __init__(self, expected: str, found: RawParsed) -> None:
        self.expected = expected
        self.found = found
    def __str__(self) -> str:
        return f'expected {self.expected}, found {self.found!r}'

class Schema:
    def parse(self, v: RawParsed) -> Any:
        raise NotImplementedError

    def __or__(self, other: 'Schema') -> 'Alternatives':
        return Alternatives([*self._get_alternatives(), *other._get_alternatives()])

    def _get_alternatives(self) -> Iterator['Schema']:
        yield self

    def wrap_in(self, fn: Callable[[Any], Any]) -> 'Wrapper':
        return Wrapper(self, fn)

@dataclass
class Wrapper(Schema):
    schema: Schema
    fn: Callable[[Any], Any]

    def parse(self, v: RawParsed) -> Any:
        return self.fn(self.schema.parse(v))

@dataclass
class Alternatives(Schema):
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
    def parse(self, v: RawParsed) -> Any:
        if not isinstance(v, str):
            raise SchemaError('string', v)
        return v

@dataclass
class Bool(Schema):
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
    def parse(self, v: RawParsed) -> Any:
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                pass
        raise SchemaError('integer', v)

@dataclass
class Float(Schema):
    def parse(self, v: RawParsed) -> Any:
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                pass
        raise SchemaError('floating point number', v)


@dataclass
class Decimal(Schema):
    def parse(self, v: RawParsed) -> Any:
        if isinstance(v, str):
            try:
                return PyDecimal(v)
            except ValueError:
                pass
        raise SchemaError('decimal number', v)

@dataclass
class Sequence(Schema):
    item: Schema

    def parse(self, v: RawParsed) -> Any:
        if not isinstance(v, list):
            raise SchemaError('sequence', v)
        return [self.item.parse(item) for item in v]

@dataclass
class Mapping(Schema):
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
    item: Schema

    def parse(self, v: RawParsed) -> Any:
        if isinstance(v, list):
            return [self.item.parse(item) for item in v]
        return [self.item.parse(v)]

@dataclass
class CommaSeparated(Schema):
    item: Schema

    def parse(self, v: RawParsed) -> Any:
        if not isinstance(v, str):
            raise SchemaError('string', v)
        return [self.item.parse(item) for item in v.split(',')]
