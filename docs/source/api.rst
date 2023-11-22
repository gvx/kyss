API
===

Basic API
---------

.. module:: kyss

.. autofunction:: parse_string

.. autofunction:: parse_file

.. autoclass:: ParsingFailure

Schemas
-------

.. data:: kyss.schema.RawParsed
   :annotation: = str | dict[str, RawParsed] | list[RawParsed]

   The type of values passed into :meth:`kyss.Schema.parse`.

.. autoclass:: Schema
   :members:

.. autoclass:: SchemaError
   :members:

.. autoclass:: Alternatives

.. autoclass:: Str

.. autoclass:: Bool

.. autoclass:: Int

.. autoclass:: Float

.. autoclass:: Decimal

.. autoclass:: Sequence

.. autoclass:: Mapping

.. autoclass:: SequenceOrSingle

.. autoclass:: CommaSeparated

.. autoclass:: Passthrough

Typed schemas
-------------

.. class:: comma_separated[T]

   Type syntax version of :py:class:`CommaSeparated`.

.. class:: list_or_single[T]

   Type syntax version of :py:class:`SequenceOrSingle`.

.. autofunction:: to_schema