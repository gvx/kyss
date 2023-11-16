import kyss

def test_scalar():
    assert kyss.parse_string('bare') == 'bare'
    assert kyss.parse_string("'single quoted'") == 'single quoted'
    assert kyss.parse_string('"double quoted"') == 'double quoted'
    assert kyss.parse_string(r'"\\ \" \' \x58 \u2714 \U0001f618"') == '\\ \" \' X \u2714 \U0001f618'

def test_simple_map():
    assert kyss.parse_string(r'''
one: '\n'
'two': '"'
''') == {"one": "\n", "two": '"'}

def test_simple_sequence():
    assert kyss.parse_string(r'''- a
- simple
- list
''') == ['a', 'simple', 'list']

def test_nested_map():
    assert kyss.parse_string(r'''outer:
    inner: okay
''') == {'outer': {'inner': 'okay'}}

def test_nested_sequence():
    assert kyss.parse_string(r'''- single
- - double
  - nested
- unnested
''') == ['single', ['double', 'nested'], 'unnested']

def test_deeply_nested_sequence():
    assert kyss.parse_string(r'''
-   - - 1
      - 2
    - 3
- - - - 4
- 5''') == [[['1', '2'], '3'], [[['4']]], '5']

def test_map_in_sequence():
    assert kyss.parse_string('- key: value\n  k2: v2') == [{'key': 'value', 'k2': 'v2'}]

def test_comments_in_map():
    assert kyss.parse_string(r'''outer: # comment
    inner: okay
''') == {'outer': {'inner': 'okay'}}
