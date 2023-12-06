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

.. autoclass:: List

.. autoclass:: Dict

.. autoclass:: ListOrSingle

.. autoclass:: CommaSeparated

.. autoclass:: Accept

Nodes
+++++

.. module:: kyss.ast

   .. autoclass:: Node()
      :members:

   .. autoclass:: ScalarNode()

      .. attribute:: kind
         :annotation: = 'scalar'

      .. autoattribute:: value

   .. autoclass:: SequenceNode()

      .. attribute:: kind
         :annotation: = 'sequence'

      .. autoattribute:: children

   .. autoclass:: MappingNode()

      .. attribute:: kind
         :annotation: = 'mapping'

      .. autoattribute:: children


Typed schemas
-------------

.. module:: kyss.typed_schema


.. class:: comma_separated[T]

   Type syntax version of :py:class:`CommaSeparated`.

.. class:: list_or_single[T]

   Type syntax version of :py:class:`ListOrSingle`.

.. autoclass:: SchemaRegistry
   :members:
