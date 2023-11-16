import pytest

import kyss

def test_invalid_escape_sequence():
    with pytest.raises(kyss.ParsingFailure) as exc:
        kyss.parse_string(r'"\f"')
    assert 'valid escape sequence' in exc.value.expected

def test_unfinished_document():
    with pytest.raises(kyss.ParsingFailure) as exc:
        kyss.parse_string('''- one
- two
foo: bar''')
    assert 'end of document' in exc.value.expected

def test_inconsistent_indentation1():
    with pytest.raises(kyss.ParsingFailure) as exc:
        kyss.parse_string('''- one: two
 three: four''')
    assert 'end of document' in exc.value.expected

def test_inconsistent_indentation2():
    with pytest.raises(kyss.ParsingFailure) as exc:
        kyss.parse_string('''key:
                                     nested:
    needs: more indentation''')
    assert 'end of document' in exc.value.expected


def test_inconsistent_indentation3():
    with pytest.raises(kyss.ParsingFailure) as exc:
        kyss.parse_string('\n:\n#')
    assert str(exc.value) == 'Expected end of document\nLine: 2\n:\n^'

    with pytest.raises(kyss.ParsingFailure) as exc:
        kyss.parse_string(':')
    assert str(exc.value) == 'Expected end of document\nLine: 1\n:\n^'

def test_unclosed():
    with pytest.raises(kyss.ParsingFailure) as exc:
        kyss.parse_string('"unclosed double quoted string')
    assert str(exc.value) == '''Expected one of {'-', "'", double quoted string contents, escape sequence, plain scalar}
Line: 1
"unclosed double quoted string
^'''
