Nginx Configuration Parser
==========================

An nginx configuration parser that uses Pyparsing.

You can parse a nginx configuration file with `load` or `loads` method:

``` {.python}
>>> from nginxparser.nginxparser import load
>>> load(open("/etc/nginx/sites-enabled/foo.conf"))

[['server'], [
    ['listen', '80'],
    ['server_name', 'foo.com'],
    ['root', '/home/ubuntu/sites/foo/']]]]
```

Same as other serialization modules also you can export configuration
with

``` {.python}
>>> from nginxparser.nginxparser import load
>>> load(open("/etc/nginx/sites-enabled/foo.conf"))

[['server'], [
    ['listen', '80'],
    ['server_name', 'foo.com'],
    ['root', '/home/ubuntu/sites/foo/']]]]
```

Same as other serialization modules also you can export configuration
with `dump` and `dumps` methods.

``` {.python}
>>> from nginxparser.nginxparser import dumps
>>> dumps([['server'], [
            ['listen', '80'],
            ['server_name', 'foo.com'],
            ['root', '/home/ubuntu/sites/foo/']]])

'server {
    listen   80;
    server_name foo.com;
    root /home/ubuntu/sites/foo/;
 }'
```

Installation
------------

The Nginx parser is now available via pip:

    git clone https://github.com/pyhedgehog/nginxparser.git;cd nginxparser;pip install .

Troubleshooting
---------------

Exception like this may occur:

    ParseException: Expected {Group:({W:(ABCD...) [{Suppress:(<SPC><TAB><CR><LF>) !W:({};)}] Suppress:(";")}) | Forward: ...} (at char 0), (line:1, col:1)

It may be caused by importing Cmd2 package which modifies pyparsing
globals. In particular, the following code causes the trouble:

``` {.python}
pyparsing.ParserElement.setDefaultWhitespaceChars(' \t')
```

In this setting the pyparser parser stops parsing after a new line.

From this reason, importing pyparsing modifies set white space chars
back to

``` {.python}
pyparsing.ParserElement.setDefaultWhitespaceChars(" \n\t\r")
```

Credits
-------

Based on the <https://github.com/fatiherikli/nginxparser> and CertBot
Nginx parser.
