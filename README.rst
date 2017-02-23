Nginx Configuration Parser
~~~~~~~~~~~~~~~~~~~~~~~~~~

An nginx configuration parser that uses Pyparsing.

You can parse a nginx configuration file with ``load`` or ``loads``
method:

.. code:: python

    >>> from nginxparser_eb import load
    >>> load(open("/etc/nginx/sites-enabled/foo.conf"))

    [['server'], [
        ['listen', '80'],
        ['server_name', 'foo.com'],
        ['root', '/home/ubuntu/sites/foo/']]]]


Same as other serialization modules also you can export configuration
with

.. code:: python

    >>> from nginxparser_eb import load
    >>> load(open("/etc/nginx/sites-enabled/foo.conf"))

    [['server'], [
        ['listen', '80'],
        ['server_name', 'foo.com'],
        ['root', '/home/ubuntu/sites/foo/']]]]


Same as other serialization modules also you can export configuration
with

.. code:: python

    >>> from nginxparser_eb import load
    >>> load(open("/etc/nginx/sites-enabled/foo.conf"))

    [['server'], [
        ['listen', '80'],
        ['server_name', 'foo.com'],
        ['root', '/home/ubuntu/sites/foo/']]]]


Same as other serialization modules also you can export configuration
with ``dump`` and ``dumps`` methods.

.. code:: python

    >>> from nginxparser_eb import dumps
    >>> dumps([['server'], [
                ['listen', '80'],
                ['server_name', 'foo.com'],
                ['root', '/home/ubuntu/sites/foo/']]])

    'server {
        listen   80;
        server_name foo.com;
        root /home/ubuntu/sites/foo/;
     }'


.. code:: python

    >>> from nginxparser_eb import dumps
    >>> dumps([['server'], [
                ['listen', '80'],
                ['server_name', 'foo.com'],
                ['root', '/home/ubuntu/sites/foo/']]])

    'server {
        listen   80;
        server_name foo.com;
        root /home/ubuntu/sites/foo/;
     }'


.. code:: python

    >>> from nginxparser_eb import dumps
    >>> dumps([['server'], [
                ['listen', '80'],
                ['server_name', 'foo.com'],
                ['root', '/home/ubuntu/sites/foo/']]])

    'server {
        listen   80;
        server_name foo.com;
        root /home/ubuntu/sites/foo/;
     }'


Installation
------------

The Nginx parser is now available via pip:

::

    pip install nginxparser_eb



Troubleshooting
---------------

Exception like this may occur:

::

    ParseException: Expected {Group:({W:(ABCD...) [{Suppress:(<SPC><TAB><CR><LF>) !W:({};)}] Suppress:(";")}) | Forward: ...} (at char 0), (line:1, col:1)

It may be caused by importing Cmd2 package which modifies pyparsing globals. In particular, the following code causes
the trouble:

.. code:: python

    pyparsing.ParserElement.setDefaultWhitespaceChars(' \t')

In this setting the pyparser parser stops parsing after a new line.

From this reason, importing pyparsing modifies set white space chars back to

.. code:: python

    pyparsing.ParserElement.setDefaultWhitespaceChars(" \n\t\r")

