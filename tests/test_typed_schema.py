import pytest
import decimal
from typing import NotRequired, TypedDict

import kyss

def test_simple_schema():
    assert kyss.parse_string('42', int) == 42

def test_decimal():
    assert kyss.parse_string('42', decimal.Decimal) == decimal.Decimal(42)

def test_one_or_more():
    assert kyss.parse_string('42', kyss.list_or_single[int]) == [42]

def test_alternatives():
    assert kyss.parse_string('3.14', int | bool | float) == 3.14

class Simple(TypedDict):
    a: int
    b: NotRequired[bool]
    _extra_: str

def test_simple_mapping():
    assert kyss.parse_string('a: 7\nb: true\nc: x', Simple) == {'a': 7, 'b': True, 'c': 'x'}

class WithoutExtra(TypedDict):
    a: int

def test_without_extra():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('a: 1\nb: 2', WithoutExtra)
    assert str(exc.value) == "Expected a mapping that only has the keys ['a'] at line 1:\na: 1\n^"

def test_simple_sequence():
    assert kyss.parse_string('- 1\n- 2\n- 3', list[int]) == [1, 2, 3]

def test_simple_sequence_or_single():
    assert kyss.parse_string('- 1\n- 2\n- 3', kyss.list_or_single[int]) == [1, 2, 3]

def test_comma_separated():
    assert kyss.parse_string('1,2,false', kyss.comma_separated[int | bool]) == [1, 2, False]

def test_mapping2():
    assert kyss.parse_string('a: b', dict[str, str]) == {'a': 'b'}

type int_or_bool = int | bool
type map_to[T] = dict[str, T]

def test_alias1():
    assert kyss.parse_string('- 1\n- True', list[int_or_bool]) == [1, True]

def test_alias2():
    assert kyss.parse_string('ok: 1\nnot okay: 2', map_to[int]) == {'ok': 1, 'not okay': 2}

def test_invalid_typed_schema():
    with pytest.raises(TypeError) as exc:
        kyss.parse_string('---', set)
    assert str(exc.value) == "invalid schema <class 'set'>"