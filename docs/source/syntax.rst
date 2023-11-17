Syntax
======

As a configuration language, kyss has three types of values:

1. Scalar values (parsed to ``str`` values)
2. Mappings of scalars to arbitrary values (parsed to ``dict`` values, where the keys are ``str`` values)
3. Sequences of arbitrary values (parsed to ``list`` values)

This makes kyss less expressive than YAML or even JSON, but the advantage is that there is a lot less syntax and less potential for visual ambiguity.

This document also contains a more formal description of the syntax.

Document
--------

A kyss document consists of a single value, possibly preceded and/or followed by empty lines and comment lines.


Grammar
^^^^^^^

.. parsed-literal::

    _`document` := newline_? value_ newline_?

    _`value` := mapping_
           | sequence_
           | scalar_

    _`newline` := (whitespace_? comment_ '\\n'){1, ...}


Whitespace
----------

In general, this document uses "whitespace" to refer to sequences of 1 or more space (``' '``, U+0020) and/or tab (``'\t'``, U+0009) characters.

Grammar
^^^^^^^

.. parsed-literal::

    _`whitespace` := /:regexp:`[ \\t]+`/

Comment
-------

Much like Python and YAML, kyss uses a hash or number sign (``'#'``) to signal the start of comments. Comments run to the end of a line.

Comments can be either on their own, preceded by optional whitespace, or on a line with other content, preceded by required whitespace.

Examples
^^^^^^^^

.. code:: yaml

    # this is a comment
    #so is this
    but#not this

    # output -> 'but#not this'

Grammar
^^^^^^^

.. parsed-literal::
    _`comment` := /:regexp:`(#.*)?`/

Scalars
-------

Kyss supports three kinds of scalars: single quoted scalars (between a pair of ``"'"`` characters), double quoted scalars (between a pair of ``'"'`` characters), and plain scalars.

Quoted scalars support escape codes. The only difference between single and double quoted scalars is that single quoted scalars can contain
unescaped double quotes and vice versa. Quoted scalars can contain arbitrary strings, as long as the following values are escaped:

* Newlines.
* Instances of the quote character used as a delimiter.
* Literal backslashes.

Plain scalars don't require delimiters, but they are more limited in what they can contain. Plain scalars **cannot** contain any newline (``'\n'``) or carriage return characters (``'\r'``).

Plain scalars **cannot** start with any of the following:

* Whitespace.
* A hyphen-minus (``'-'``) followed by whitespace.
* A quote character (``'"'`` or ``"'"``).

Plain scalars can also **not** contain the following sequences of characters:

* A colon (``':'``) followed by whitespace.
* A hash or number sign (``'#'``) preceded by whitespace.

Plain scalars can end in whitespace, but it is stripped from the output.

Escape sequences
^^^^^^^^^^^^^^^^

The following escape sequences are allowed:

* ``\\`` for a literal backslash.
* ``\'`` for a literal single quote.
* ``\"`` for a literal double quote.
* ``\t`` for a tab (same as ``\x09``.
* ``\n`` for a newline (same as ``\x0a``).
* ``\r`` for a carriage return (same as ``\x0d``).
* ``\x••``, ``\u••••`` and ``\U••••••••`` (where ``•`` is a case insensitive hexadecimal digit) for arbitrary unicode code points.

Examples
^^^^^^^^

::

    - this is a scalar value
    - "so is this"
    - 'and this'
    - "" # empty scalar
    - "Some escape codes: \n \r \t \" \' \\ \x40 \u0040 \U00000040"

    # output -> ['this is a scalar value', 'so is this', 'and this', '', 'Some escape codes: \n \r \t " \' \\ @ @ @']

Grammar
^^^^^^^

.. parsed-literal::

    _`scalar` := plain_scalar_ | single_quoted_ | double_quoted_

    _`plain_scalar` := /:regexp:`(?!-[ \\t]|['" \\t])(:[^ \\t\\n]|[^ \\t\\n]#|[^:#\\n])*`/

    _`single_quoted` := "'" (/:regexp:`[^'\\n\\\\]+`/ | escape_sequence_){0, ...} "'"

    _`double_quoted` := '"' (/:regexp:`[^"\\n\\\\]+`/ | escape_sequence_){0, ...} '"'

    _`escape_sequence` := /:regexp:`\\\\(x[a-fA-F0-9]{2}|u[a-fA-F0-9]{4}|U[a-fA-F0-9]{8})`/

Indentation
-----------

Kyss uses significant indentation, which consists of whitespace at the beginning of a line that contains a mapping key/value pair or a sequence item. I personally favour 2 spaces of indentation, but the only rules are the following:

1. The indentation for each key/value pair or sequence item of a single mapping or sequence has to be the exact same string.
2. The indentation for mappings and sequences that are values in a mapping is equal to the indentation of the containing mapping, plus a suffix of one or more whitespace characters.
3. The indentation for mappings and sequences that are sequence items is equal to the indentation of the containing sequence, plus a single space, plus the whitespace characters between the ``-`` character marking the sequence item and the first following non-whitespace character.

In the grammar fragments in this document, indentation is described using ``indent`` and ``dedent`` virtual tokens.

Mappings
--------

Mappings resemble YAML simple block style mappings. They contain one or more key/value pairs, with newlines (``\n``) between pairs.

Keys are scalar values (either quoted or plain).

If the associated value is a scalar, it is on the same line as the key.

If the associated value is a mapping or sequence, they start on the next line, in an indented block.

Examples
^^^^^^^^

.. code:: yaml

    key 1: value 1
    "can be quoted": # comment
      nested: true # comment

    # more than one newline and comments between pairs allowed

      location: inner
    location: outer

    # output -> {'key 1': 'value 1', 'can be quoted': {'nested': 'true', 'location': 'inner'}, 'location': 'outer'}

Grammar
^^^^^^^

.. parsed-literal::

    _`mapping` := mapping_item_ (newline_ mapping_item_){0, ...}

    _`mapping_item` := scalar_ ':' mapping_value_

    _`mapping_value` := whitespace_ scalar_
                   \| `indent <Indentation_>`_ newline_ (sequence_ \| mapping_) `dedent <Indentation_>`_

Sequences
---------

Sequences resemble YAML block style sequences. They contain one or more sequence items, with newlines (``\n``) between items.

A sequence item starts with a hyphen-minus (``'-'``), followed by whitespace and a value.

If a sequence item describes a mapping or sequence, its indented block begins on the same line as the hyphen-minus.

Examples
^^^^^^^^

.. code:: yaml

    - cheese
    - bread
    - - sugar
      - spice # comment
      - everything nice
    - tea

       # comment

    - mapping: nested
      allowed: true
    -     more whitespace: than
          strictly: necessary
    -            - ok
                 - fine

    # output -> ['cheese', 'bread', ['sugar', 'spice', 'everything nice'], 'tea', {'mapping': 'nested', 'allowed': 'true'}, {'more whitespace': 'than', 'strictly': 'necessary'}, ['ok', 'fine']]

Grammar
^^^^^^^

.. parsed-literal::

    _`sequence` := sequence_item_ (newline_ sequence_item_){0, ...}

    _`sequence_item` := '-' sequence_item_value_

    _`sequence_item_value` := whitespace_ scalar_
                         | `indent <Indentation_>`_ whitespace_ (sequence_ | mapping_) `dedent <Indentation_>`_
