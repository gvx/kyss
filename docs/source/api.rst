API
===

Basic API
---------

.. module:: kyss

.. autofunction:: parse_string

.. autofunction:: parse_file

.. autoclass:: kyss.ParsingFailure

Schemas
-------

.. autoclass:: kyss.Schema
   :members:

.. autoclass:: kyss.SchemaError
   :members:

.. autoclass:: kyss.Alternatives

.. autoclass:: kyss.Str

.. autoclass:: kyss.Bool

.. autoclass:: kyss.Int

.. autoclass:: kyss.Float

.. autoclass:: kyss.Decimal

.. autoclass:: kyss.Sequence

.. autoclass:: kyss.Mapping

.. autoclass:: kyss.SequenceOrSingle

.. autoclass:: kyss.CommaSeparated

Typed schemas
-------------

.. autoclass:: comma_separated

   Type version of :py:class:`CommaSeparated`.

.. autoclass:: list_or_single

   Type version of :py:class:`SequenceOrSingle`.

.. autofunction:: to_schema