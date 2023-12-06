from collections.abc import Iterable
from decimal import Decimal as PyDecimal
from inspect import get_annotations
from os import PathLike
from pathlib import Path
from types import UnionType
from typing import (Any, NotRequired, Required, TypeAliasType, get_args,
                    get_origin, is_typeddict)

from .recursive_descent import parse
from .schema import (Accept, Alternatives, Bool, CommaSeparated, Decimal, Dict,
                     Float, Int, List, ListOrSingle, Schema, Str)


class list_or_single[T](list[T]):
    pass


class comma_separated[T](list[T]):
    pass


class SchemaRegistry:
    def __init__(self) -> None:
        self.schema_builders = {bool: Bool, str: Str, int: Int, float: Float,
                                PyDecimal: Decimal, Any: Accept,
                                list_or_single: ListOrSingle,
                                comma_separated: CommaSeparated}

    def _mapping_specified(self, value_types: dict[str, type], keys: Iterable[str]) -> dict[str, Schema]:
        return {key: self.to_schema(value_types[key]) for key in keys if key != '_extra_'}

    def register_type(self, type_: type, schema_builder: type[Schema]) -> None:
        '''Add or override a type. After ``registry.register_type(MyType, MySchema)``,
        ``registry.to_schema(MyType)`` → ``MySchema()`` and ``registry.to_schema(MyType[A, B])`` → ``MySchema(registry.to_schema(A), registry.to_schema(B))``.'''

        self.schema_builders[type_] = schema_builder

    def to_schema(self, type_schema: type | Schema) -> Schema:
        r'''Interpret a type as a schema. Called by :py:func:`parse_string` and :py:func:`parse_file`.

        By default, it operates like this:

        - ``registry.to_schema(str)`` → :class:`kyss.Str`\ ``()``
        - ``registry.to_schema(int)`` → :class:`kyss.Int`\ ``()``
        - ``registry.to_schema(bool)`` → :class:`kyss.Bool`\ ``()``
        - ``registry.to_schema(float)`` → :class:`kyss.Float`\ ``()``
        - ``registry.to_schema(``:class:`decimal.Decimal`\ ``)`` → :class:`kyss.Decimal`\ ``()``
        - ``registry.to_schema(``:external:data:`typing.Any`\ ``)`` → :class:`kyss.Accept`\ ``()``
        - ``registry.to_schema(list[★])`` → :class:`kyss.List`\ ``(registry.to_schema(★))``
        - ``registry.to_schema(dict[str, ★])`` → :class:`kyss.Dict`\ ``({}, registry.to_schema(★))``
        - ``registry.to_schema(``:class:`list_or_single`\ ``[★])`` → :class:`kyss.ListOrSingle`\ ``(registry.to_schema(★))``
        - ``registry.to_schema(``:class:`comma_separated`\ ``[★])`` → :class:`kyss.CommaSeparated`\ ``(registry.to_schema(★))``
        - ``registry.to_schema(★ | ♦)`` → ``registry.to_schema(★) | registry.to_schema(♦)``

        - Given

            ::

                type spam = int
                type ham[T] = list[T]

            - ``registry.to_schema(spam)`` → :class:`kyss.Int`\ ``()``
            - ``registry.to_schema(ham[bool])`` → :class:`kyss.List`\ ``(``:class:`kyss.Bool`\ ``())``

        - Given

            .. parsed-literal::

                class Employee(:external:class:`typing.TypedDict`\ ):
                    id: int
                    department: :external:data:`typing.NotRequired`\ [str]

                    _extra_: bool

            - ``registry.to_schema(Employee)`` → :class:`kyss.Dict`\ ``({'id':`` :class:`kyss.Int`\ ``()},`` :class:`kyss.Bool`\ ``(), optional={'department':`` :class:`kyss.Str`\ ``()})``

        '''
        if isinstance(type_schema, Schema):
            return type_schema
        if isinstance(type_schema, TypeAliasType):
            return self.to_schema(type_schema.__value__)
        if type_schema in self.schema_builders:
            return self.schema_builders[type_schema]()
        if is_typeddict(type_schema):
            value_types = get_annotations(type_schema)
            required: frozenset[str] = type_schema.__required_keys__  # type: ignore
            optional: frozenset[str] = type_schema.__optional_keys__  # type: ignore
            extra: Schema | None = None
            if '_extra_' in value_types and value_types['_extra_'] is not None:
                extra = self.to_schema(value_types['_extra_'])
            return Dict(self._mapping_specified(value_types, required), extra,
                        optional=self._mapping_specified(value_types, optional))
        origin = get_origin(type_schema)
        if origin is UnionType:
            return Alternatives([self.to_schema(alt) for alt in get_args(type_schema)])
        elif isinstance(origin, TypeAliasType):
            return self.to_schema(origin.__value__[get_args(type_schema)])
        elif origin in self.schema_builders:
            return self.schema_builders[origin](*map(self.to_schema, get_args(type_schema)))
        elif origin is list:
            return List(self.to_schema(get_args(type_schema)[0]))
        elif origin is dict:
            t_key, t_value = get_args(type_schema)
            assert t_key is str
            return Dict({}, self.to_schema(t_value))
        elif origin in {Required, NotRequired}:
            return self.to_schema(get_args(type_schema)[0])
        raise TypeError(f'invalid schema {type_schema!r}')

    def parse_string(self, s: str, /, schema: Schema | type = Accept()) -> Any:
        '''Parse a kyss string. If a Schema or type schema is provided, it will be used to validate the parsed value

        :param s: a str that contains the kyss-encoded value
        :param schema: optional schema to use'''

        return self.to_schema(schema).validate(parse(s))

    def parse_file(self, f: PathLike[str], /, schema: Schema | type = Accept()) -> Any:
        '''Parse a kyss file (utf-8 encoded). If a Schema or type schema is provided, it will be used to validate the parsed value

        :param f: a os.PathLike for the file name
        :param schema: optional schema to use'''

        return self.parse_string(Path(f).read_text(encoding='utf-8'), schema)


default_registry = SchemaRegistry()

parse_string = default_registry.parse_string
parse_file = default_registry.parse_file