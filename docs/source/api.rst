API
===

Basic API
---------

.. module:: kyss

.. autofunction:: parse_string

.. autofunction:: parse_file

.. autoclass:: KyssError

.. autoclass:: KyssSyntaxError

.. autoclass:: KyssSchemaError

Schemas
-------

.. autoclass:: Schema
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

.. autoclass:: Accept

Typed schemas
-------------

.. class:: comma_separated[T]

   Type syntax version of :py:class:`CommaSeparated`.

.. class:: list_or_single[T]

   Type syntax version of :py:class:`SequenceOrSingle`.

.. autoclass:: SchemaRegistry
   :members:
