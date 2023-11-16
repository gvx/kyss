import pytest
from tempfile import NamedTemporaryFile

import kyss
import kyss.recursive_descent

from kyss.recursive_descent import Source, ParsingFailure, n_or_more

def test_n_or_more():
    with pytest.raises(ParsingFailure) as exc:
        def expect_x(s: Source) -> tuple[None, Source]:
            return None, s.expect('x')
        n_or_more(Source('xxx'), expect_x, 4)
    assert "At least 4 times 'x'" in exc.value.expected

def test_read_file():
    with NamedTemporaryFile('w+', encoding='utf-8', delete_on_close=False) as tmp:
        tmp.write('ok\n')
        tmp.close()
        assert kyss.parse_file(tmp.name) == 'ok'