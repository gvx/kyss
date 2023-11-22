import sys
from argparse import ArgumentParser, FileType
from pathlib import Path

from .__about__ import __version__
from .recursive_descent import parse_file, parse_string


def maybe_path(s: str) -> Path | None:
    if s == '-':
        return None
    return Path(s)

argument_parser = ArgumentParser('kyss', description='Read kyss format files')
argument_parser.add_argument('--version', action='version', version=f'kyss {__version__}')
argument_parser.add_argument('source', default=None, help='File to read from (standard input by default)', nargs='?', type=maybe_path)
argument_parser.add_argument('dest', default=None, help='File to write to (standard output by default)', nargs='?', type=maybe_path)
argument_parser.add_argument('--schema', '-s', action='store', help='Optional schema, either as argument or a path preceded by @')
argument_parser.add_argument('--format', '-f', action='store', choices={'python', 'json'}, default='python', help='The way to express the output')

if __name__ == '__main__':
    args = argument_parser.parse_args()

    schema = None

    if args.schema:
        from .schema_file import read_schema_file, read_schema_string

        if args.schema.startswith('@'):
            schema = read_schema_file(args.schema.removeprefix('@'))
        else:
            schema = read_schema_string(args.schema)

    if args.source is None:
        value = parse_string(sys.stdin.read(), schema)
    else:
        value = parse_file(args.source, schema)

    if args.format == 'python':
        output = repr(value)
    elif args.format == 'json':
        import json
        output = json.dumps(value, indent=2)

    if args.dest is None:
        sys.stdout.write(output)
    else:
        args.dest.write_text(output)
