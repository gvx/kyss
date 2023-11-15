import ast
from pathlib import Path
from typing import NotRequired, Required, TypedDict

from .schema import (Bool, CommaSeparated, Decimal, Float, Int, Mapping,
                     Schema, Sequence, SequenceOrSingle, Str)
from .typed_schema import comma_separated, list_or_single, to_schema

AVAILABLE_SYMBOLS = {
    # from typing:
    TypedDict, Required, NotRequired,
    # from .schema:
    Schema, Str, Int, Float, Decimal, Bool, Sequence, Mapping, SequenceOrSingle, CommaSeparated,
    # from .typed_schema:
    list_or_single, comma_separated, to_schema
}

def fresh_schema_env() -> dict:
    return {sym.__name__: sym for sym in AVAILABLE_SYMBOLS}

def read_schema_file(schema_filename: str) -> Schema:
    tree = ast.parse(Path(schema_filename).read_text(encoding='utf-8'))
    last_stmt = tree.body.pop()
    if not isinstance(last_stmt, ast.Expr):
        raise SyntaxError('last statement of schema file should be an expression containing the schema')
    schema_globals = fresh_schema_env()
    exec(compile(tree, schema_filename, 'exec'), schema_globals)
    return to_schema(eval(compile(ast.Expression(last_stmt.value), schema_filename, 'eval'), schema_globals))

def read_schema_string(schema_text: str) -> Schema:
    return to_schema(eval(schema_text, fresh_schema_env()))