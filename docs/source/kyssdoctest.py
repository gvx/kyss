'''very crude way to get doctest-like behaviour for kyss samples'''

from pathlib import Path

import kyss

prefix = '''
Examples
^^^^^^^^

'''

suffix = '''
Grammar
^^^^^^^
'''

text = (Path(__file__).parent / 'syntax.rst').read_text()

start_index = 0
while (start_index := text.find(prefix, start_index)) > -1:
    start_index += len(prefix)
    end_index = text.index(suffix, start_index)
    fragment = text[start_index:end_index]
    start_index = end_index + len(suffix)
    fragment = fragment.replace('\n    ', '\n') # simple dedent
    fragment.removeprefix('::\n').removeprefix('.. code:: yaml')
    _, expected_output = fragment.split('output ->')
    try:
        actual_output = repr(kyss.parse_string(fragment))
    except kyss.ParsingFailure as e:
        print('ERROR, could not parse:')
        print(fragment)
        print(e)
    else:
        if expected_output.strip() != actual_output:
            print('DIFFERENCE')
            print('Expe.:', expected_output.strip())
            print('Found:', actual_output)
        else:
            print('OK')
