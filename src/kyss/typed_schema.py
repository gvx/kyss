from collections.abc import Iterable
from decimal import Decimal as PyDecimal
from inspect import get_annotations
from types import UnionType
from typing import (NotRequired, Required, TypeVar, get_args, get_origin,
                    is_typeddict, TypeAliasType)

from .schema import (Alternatives, Bool, CommaSeparated, Decimal, Float, Int,
                     Mapping, Schema, Sequence, SequenceOrSingle, Str)

TERMINAL_MAPPING: dict[type, Schema] = {bool: Bool(), str: Str(), int: Int(), float: Float(), PyDecimal: Decimal()}

# list[T] -> Sequence(to_schema(T))
# dict[str, T] -> Mapping({}, to_schema(T))
# TypedDict('SomeTypedDict', {'a': int, 'b': NotRequired[bool], '_extra_': list[str]}) -> Mapping({'a': Int()}, Sequence(Str()), {'b': Bool()})

class list_or_single[T](list[T]):
    pass

class comma_separated[T](list[T]):
    pass

def _mapping_specified(value_types: dict[str, type], keys: Iterable[str]) -> dict[str, Schema]:
    return {key: to_schema(value_types[key]) for key in keys if key != '_extra_'}

def to_schema(type_schema: type | Schema) -> Schema:
    if isinstance(type_schema, Schema):
        return type_schema
    if isinstance(type_schema, TypeAliasType):
        return to_schema(type_schema.__value__)
    if type_schema in TERMINAL_MAPPING:
        return TERMINAL_MAPPING[type_schema]
    if is_typeddict(type_schema):
        value_types = get_annotations(type_schema)
        required: frozenset[str] = type_schema.__required_keys__  # type: ignore
        optional: frozenset[str] = type_schema.__optional_keys__  # type: ignore
        extra: Schema | None = None
        if '_extra_' in value_types and value_types['_extra_'] is not None:
            extra = to_schema(value_types['_extra_'])
        return Mapping(_mapping_specified(value_types, required), extra, optional=_mapping_specified(value_types, optional))
    origin = get_origin(type_schema)
    if origin is UnionType:
        return Alternatives([to_schema(alt) for alt in get_args(type_schema)])
    elif origin is list:
        return Sequence(to_schema(get_args(type_schema)[0]))
    elif origin is dict:
        t_key, t_value = get_args(type_schema)
        assert t_key is str
        return Mapping({}, to_schema(t_value))
    elif origin is list_or_single:
        return SequenceOrSingle(to_schema(get_args(type_schema)[0]))
    elif origin is comma_separated:
        return CommaSeparated(to_schema(get_args(type_schema)[0]))
    elif origin in {Required, NotRequired}:
        return to_schema(get_args(type_schema)[0])
    elif isinstance(origin, TypeAliasType):
        return to_schema(origin.__value__[get_args(type_schema)])
    raise TypeError(f'invalid schema {type_schema!r}')
