import pytest
import decimal

import kyss

def test_simple_schema():
    assert kyss.parse_string('42', kyss.Int()) == 42

def test_decimal():
    assert kyss.parse_string('42', kyss.Decimal()) == decimal.Decimal(42)

def test_one_or_more():
    assert kyss.parse_string('42', kyss.ListOrSingle(kyss.Int())) == [42]

def test_alternatives():
    assert kyss.parse_string('3.14', kyss.Int() | kyss.Bool() | kyss.Float()) == 3.14

def test_simple_mapping():
    assert kyss.parse_string('a: 7\nb: true\nc: x', kyss.Dict({'a': kyss.Int()}, kyss.Str(), optional={'b': kyss.Bool()})) == {'a': 7, 'b': True, 'c': 'x'}

def test_simple_sequence():
    assert kyss.parse_string('- 1\n- 2\n- 3', kyss.List(kyss.Int())) == [1, 2, 3]

def test_simple_sequence_or_single():
    assert kyss.parse_string('- 1\n- 2\n- 3', kyss.ListOrSingle(kyss.Int())) == [1, 2, 3]

def test_comma_separated():
    assert kyss.parse_string('1,2,false', kyss.CommaSeparated(kyss.Int() | kyss.Bool())) == [1, 2, False]

def test_invalid_int():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('3a', kyss.Int())
    assert str(exc.value) == "Expected integer at line 1:\n3a\n^"

def test_invalid_bool():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('yes', kyss.Bool())
    assert str(exc.value) == "Expected true or false at line 1:\nyes\n^"

def test_invalid_float():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('3a', kyss.Float())
    assert str(exc.value) == "Expected floating point number at line 1:\n3a\n^"

def test_invalid_multiple():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('3a', kyss.Float() | kyss.Bool() | kyss.Decimal())
    assert list(exc.value.expected) == ['floating point number', 'true or false', 'decimal number']

def test_invalid_str():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('a: b', kyss.Str())
    assert str(exc.value) == "Expected string at line 1:\na: b\n^"

def test_found_nonscalar1():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('a: b', kyss.Int())
    assert str(exc.value) == "Expected integer at line 1:\na: b\n^"

def test_found_nonscalar2():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('a: b', kyss.Float())
    assert str(exc.value) == "Expected floating point number at line 1:\na: b\n^"

def test_found_nonscalar3():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('a: b', kyss.Bool())
    assert str(exc.value) == "Expected true or false at line 1:\na: b\n^"

def test_found_nonscalar4():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('a: b', kyss.Decimal())
    assert str(exc.value) == "Expected decimal number at line 1:\na: b\n^"

def test_found_nonscalar5():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('a: b', kyss.CommaSeparated(kyss.Str()))
    assert str(exc.value) == "Expected string at line 1:\na: b\n^"

def test_wrappers():
    assert kyss.parse_string('test', kyss.Str().wrap_in(len)) == 4

def test_invalid_mapping1():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('a:b', kyss.Dict({'a': kyss.Str()}))
    assert str(exc.value) == "Expected mapping at line 1:\na:b\n^"

def test_invalid_mapping2():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('b: b', kyss.Dict({'a': kyss.Str()}))
    assert str(exc.value) == "Expected a mapping that has the keys ['a'] at line 1:\nb: b\n^"

def test_invalid_mapping3():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('a: b\nb: b', kyss.Dict({'a': kyss.Str()}))
    assert str(exc.value) == "Expected a mapping that only has the keys ['a'] at line 1:\na: b\n^"

def test_invalid_sequence():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('a: b\nb: b', kyss.List(kyss.Str()))
    assert str(exc.value) == "Expected sequence at line 1:\na: b\n^"

def test_mapping2():
    assert kyss.parse_string('a: b', kyss.Dict({'a': kyss.Str()})) == {'a': 'b'}

def test_parse_needs_implementing():
    with pytest.raises(NotImplementedError):
        kyss.Schema().validate('not a node')

def test_wrapper_validates():
    with pytest.raises(kyss.KyssSchemaError) as exc:
        kyss.parse_string('3a', kyss.Str().wrap_in(int, 'integer'))
    assert 'integer' in exc.value.expected