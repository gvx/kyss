Usage
=====

Tutorial
--------

Basics
++++++

The most common usages of kyss will be to simply pass a string into :func:`kyss.parse_string` or a path into :func:`kyss.parse_file`.

The exact syntax is explained in :doc:`syntax`, but here are a couple of simple examples:

.. code:: yaml

    - sequence
    - of
    - "scalars"

    # output -> ['sequence', 'of', 'scalars']

.. code:: yaml

    mapping: yes
    type: simple

    # output -> {'mapping': 'yes', 'type': 'simple'}

.. code:: yaml

    - actor: Christopher Eccleston
      regeneration: 9
    - actor: David Tennant
      regeneration: 10
    - actor: Matt Smith
      regeneration: 11
    - actor: Peter Capaldi
      regeneration: 12
    - actor: Jodie Whittaker
      regeneration: 13

    # output -> [{'actor': 'Christopher Eccleston', 'regeneration': '9'},
    #            {'actor': 'David Tennant', 'regeneration': '10'},
    #            {'actor': 'Matt Smith', 'regeneration': '11'},
    #            {'actor': 'Peter Capaldi', 'regeneration': '12'},
    #            {'actor': 'Jodie Whittaker', 'regeneration': '13'}]

Note how the only types being returned by parsing these examples are ``str``\s, ``list``\s and ``dict``\s.

Schemas
+++++++

In order to impose some sort of structure on kyss documents, you can pass a schema as the second argument to :func:`kyss.parse_string` or :func:`kyss.parse_file`.

For example::

    from pprint import pprint

    import kyss

    regeneration_schema = kyss.Dict({'actor': kyss.Str(),
                                     'regeneration': kyss.Int()})

    example3 = '''...''' # paste in the text from the previous example
    pprint(kyss.parse_string(example3, schema=kyss.List(regeneration_schema)))

    # output:
    # [{'actor': 'Christopher Eccleston', 'regeneration': 9},
    #  {'actor': 'David Tennant', 'regeneration': 10},
    #  {'actor': 'Matt Smith', 'regeneration': 11},
    #  {'actor': 'Peter Capaldi', 'regeneration': 12},
    #  {'actor': 'Jodie Whittaker', 'regeneration': 13}]

Now, suppose we want to add David Tennant's new character the Fourteenth Doctor, and we only want to have each actor occur once. We could do something like the following::

    from pprint import pprint

    import kyss

    regeneration_schema = kyss.Dict({'actor': kyss.Str(),
                                     'regeneration': kyss.ListOrSingle(kyss.Int())})

    example4 = '''
    - actor: Christopher Eccleston
      regeneration: 9
    - actor: David Tennant
      regeneration:
        - 10
        - 14
    - actor: Matt Smith
      regeneration: 11
    - actor: Peter Capaldi
      regeneration: 12
    - actor: Jodie Whittaker
      regeneration: 13
    '''
    pprint(kyss.parse_string(example4, schema=kyss.List(regeneration_schema)))

    # output:
    # [{'actor': 'Christopher Eccleston', 'regeneration': [9]},
    #  {'actor': 'David Tennant', 'regeneration': [10, 14]},
    #  {'actor': 'Matt Smith', 'regeneration': [11]},
    #  {'actor': 'Peter Capaldi', 'regeneration': [12]},
    #  {'actor': 'Jodie Whittaker', 'regeneration': [13]}]

Using :class:`kyss.ListOrSingle` means that the value associated with ``'regeneration'`` is always a list of integers.

If you want more control over how data gets interpreted, you can subclass :class:`kyss.Schema`, and override :meth:`kyss.Schema.parse`. It should raise :exc:`kyss.SchemaError` if the data doesn't fit your schema.

.. TODO: advanced uses of Dict
.. TODO: Alternatives
.. TODO: wrap_in
.. TODO: writing your own schemas

Typed schemas
+++++++++++++

You may have noticed that schema definitions can get rather unwieldy. Because of that, instead of a schema you can also pass a Python type annotation that describes the shape of the data, that covers most of what you can do with regular schemas.

For example::

    example = '''
    alice:
      - first: 32
      - other: 1
    bob:
      - last: 6
    '''
    pprint(kyss.parse_string(example, dict[str, list[dict[str, int]]]))

    # output:
    # {'alice': [{'first': 32}, {'other': 1}], 'bob': [{'last': 6}]}

You can use :class:`typing.TypedDict` to describe more mappings with specified keys, for example::

    import typing

    example = '''
    - name: Guido van Rossum
      title: former BDFL
    - name: Python
      major version: 3
      minor version: 12
    '''

    class Person(typing.TypedDict):
        name: str
        title: str

    ProgrammingLanguage = typing.TypedDict('ProgrammingLanguage',
            {'name': str, 'major version': int,
             'minor version': int, 'braces': typing.NotRequired[bool]})

    pprint(kyss.parse_string(example, list[Person | ProgrammingLanguage]))

    # output:
    # [{'name': 'Guido van Rossum', 'title': 'former BDFL'},
    #  {'major version': 3, 'minor version': 12, 'name': 'Python'}]

If you want to use custom :class:`kyss.Schema` subclasses or  :meth:`kyss.Schema.wrap_in`, you can add them to a :class:`SchemaRegistry`::

    from dataclasses import dataclass

    registry = kyss.SchemaRegistry()

    @dataclass
    class Tuple(kyss.Schema):
        item: kyss.Schema

        def validate(self, node: kyss.ast.Node) -> tuple:
            if not isinstance(node, kyss.ast.ListNode):
                raise kyss.schema.schema_error(node, 'sequence')
            return [self.item.validate(item) for item in node.children]

    def make_set_schema(*args):
        return kyss.List(*args).wrap_in(set)

    registry.register_type(set, make_set_schema)

    example = '''
    - - 10
    - - 20
      - 30
    - - 40
      - 50
    '''

    pprint(registry.parse_string(example, set[tuple[int]]))

    # output:
    # {(10,), (20, 30), (40, 50)}
