"""Test for certbot_nginx.nginxparser."""
import copy
import operator
import tempfile
import unittest
import pkg_resources
import os
import pprint
import types

from pyparsing import ParseException
from nginxparser_eb import (load, loads, dump, dumps, NginxParser, NginxDumper, UnspacedList,
                            find_elems, find_in_model, build_model, BaseDirective, BlockDirective)


FIRST = operator.itemgetter(0)


def get_data_filename(filename):
    """Gets the filename of a test data file."""
    return pkg_resources.resource_filename(
        "nginxparser_eb.tests", os.path.join(
            "test_data", "etc_nginx", filename))


class TestNginxParser(unittest.TestCase):
    """Test the raw low-level Nginx config parser."""
    
    def test_assignments(self):
        parsed = NginxParser.assignment.parseString('root /test;').asList()
        self.assertEqual(parsed, ['root', ' ', '/test'])
        parsed = NginxParser.assignment.parseString('root /test;foo bar;').asList()
        self.assertEqual(parsed, ['root', ' ', '/test'], ['foo', ' ', 'bar'])

    def test_blocks(self):
        parsed = NginxParser.block.parseString('foo {}').asList()
        self.assertEqual(parsed, [[['foo', ' '], []]])
        parsed = NginxParser.block.parseString('location /foo{}').asList()
        self.assertEqual(parsed, [[['location', ' ', '/foo'], []]])
        parsed = NginxParser.block.parseString('foo { bar foo ; }').asList()
        self.assertEqual(parsed, [[['foo', ' '], [[' ', 'bar', ' ', 'foo '], ' ']]])

    def test_nested_blocks(self):
        parsed = NginxParser.block.parseString('foo { bar {} }').asList()
        block, content = FIRST(parsed)
        self.assertEqual(FIRST(content), [[' ', 'bar', ' '], []])
        self.assertEqual(FIRST(block), 'foo')

    def test_dump_as_string(self):
        dumped = dumps(UnspacedList([
            ['user', ' ', 'www-data'],
            [['\n', 'server', ' '], [
                ['\n    ', 'listen', ' ', '80'],
                ['\n    ', 'server_name', ' ', 'foo.com'],
                ['\n    ', 'root', ' ', '/home/ubuntu/sites/foo/'],
                [['\n\n    ', 'location', ' ', '/status', ' '], [
                    ['\n        ', 'check_status', ''],
                    [['\n\n        ', 'types', ' '],
                    [['\n            ', 'image/jpeg', ' ', 'jpg']]],
                ]]
            ]]]))

        self.assertEqual(dumped.split('\n'),
                         'user www-data;\n'
                         'server {\n'
                         '    listen 80;\n'
                         '    server_name foo.com;\n'
                         '    root /home/ubuntu/sites/foo/;\n'
                         '\n'
                         '    location /status {\n'
                         '        check_status;\n'
                         '\n'
                         '        types {\n'
                         '            image/jpeg jpg;}}}'.split('\n'))
        
    def test_complex(self):
        """
        Testing load/dump consistency
        :return: 
        """
        with open(get_data_filename('complex.conf')) as handle:
            parsed = load(handle)

            # Dump it
            dumped = dumps(parsed)

            # Parse again, now as text
            parsed2 = loads(dumped)

            # Dump again
            dumped2 = dumps(parsed2)
            self.assertEqual(dumped, dumped2)

    def test_find(self):
        """
        Finding directives in the config file
        :return: 
        """
        with open(get_data_filename('complex.conf')) as handle:
            parsed = load(handle)
            roots = find_elems(parsed, ['http', 'server', 'root'])
            self.assertEqual(roots, ['/usr/share/nginx/html', '/usr/share/nginx/html'])

    def test_model(self):
        with open(get_data_filename('complex.conf')) as handle:
            parsed = load(handle)
            model = build_model(parsed)
            self.assertTrue(isinstance(model, BlockDirective))

    def test_find_in_model(self):
        with open(get_data_filename('complex.conf')) as handle:
            parsed = load(handle)
            model = build_model(parsed)
            res = find_in_model(model, ['http', 'server', 'root'])

            self.assertTrue(isinstance(res, types.ListType))
            self.assertEqual(len(res), 2)

            for x in res:
                self.assertTrue(isinstance(x, BaseDirective))
                self.assertEqual(x.key, 'root')
                self.assertEqual(x.value, '/usr/share/nginx/html')
                self.assertTrue(x.parent is not None)
                self.assertTrue(isinstance(x.parent, BlockDirective))
                # pprint.pprint(x)
                # pprint.pprint(x.parent)


class TestUnspacedList(unittest.TestCase):
    """Test the UnspacedList data structure"""
    def setUp(self):
        self.a = ["\n    ", "things", " ", "quirk"]
        self.b = ["y", " "]
        self.l = self.a[:]
        self.l2 = self.b[:]
        self.ul = UnspacedList(self.l)
        self.ul2 = UnspacedList(self.l2)

    def test_construction(self):
        self.assertEqual(self.ul, ["things", "quirk"])
        self.assertEqual(self.ul2, ["y"])

    def test_append(self):
        ul3 = copy.deepcopy(self.ul)
        ul3.append("wise")
        self.assertEqual(ul3, ["things", "quirk", "wise"])
        self.assertEqual(ul3.spaced, self.a + ["wise"])

    def test_add(self):
        ul3 = self.ul + self.ul2
        self.assertEqual(ul3, ["things", "quirk", "y"])
        self.assertEqual(ul3.spaced, self.a + self.b)
        self.assertEqual(self.ul.spaced, self.a)
        ul3 = self.ul + self.l2
        self.assertEqual(ul3, ["things", "quirk", "y"])
        self.assertEqual(ul3.spaced, self.a + self.b)

    def test_extend(self):
        ul3 = copy.deepcopy(self.ul)
        ul3.extend(self.ul2)
        self.assertEqual(ul3, ["things", "quirk", "y"])
        self.assertEqual(ul3.spaced, self.a + self.b)
        self.assertEqual(self.ul.spaced, self.a)

    def test_set(self):
        ul3 = copy.deepcopy(self.ul)
        ul3[0] = "zither"
        l = ["\n ", "zather", "zest"]
        ul3[1] = UnspacedList(l)
        self.assertEqual(ul3, ["zither", ["zather", "zest"]])
        self.assertEqual(ul3.spaced, [self.a[0], "zither", " ", l])

    def test_get(self):
        self.assertRaises(IndexError, self.ul2.__getitem__, 2)
        self.assertRaises(IndexError, self.ul2.__getitem__, -3)

    def test_insert(self):
        x = UnspacedList(
                [['\n    ', 'listen', '       ', '69.50.225.155:9000'],
                ['\n    ', 'listen', '       ', '127.0.0.1'],
                ['\n    ', 'server_name', ' ', '.example.com'],
                ['\n    ', 'server_name', ' ', 'example.*'], '\n',
                ['listen', ' ', '5001 ssl']])
        x.insert(5, "FROGZ")
        self.assertEqual(x,
            [['listen', '69.50.225.155:9000'], ['listen', '127.0.0.1'],
            ['server_name', '.example.com'], ['server_name', 'example.*'],
            ['listen', '5001 ssl'], 'FROGZ'])
        self.assertEqual(x.spaced,
            [['\n    ', 'listen', '       ', '69.50.225.155:9000'],
            ['\n    ', 'listen', '       ', '127.0.0.1'],
            ['\n    ', 'server_name', ' ', '.example.com'],
            ['\n    ', 'server_name', ' ', 'example.*'], '\n',
            ['listen', ' ', '5001 ssl'],
            'FROGZ'])

    def test_rawlists(self):
        ul3 = copy.deepcopy(self.ul)
        ul3.insert(0, "some")
        ul3.append("why")
        ul3.extend(["did", "whether"])
        del ul3[2]
        self.assertEqual(ul3, ["some", "things", "why", "did", "whether"])

    def test_is_dirty(self):
        self.assertEqual(False, self.ul2.is_dirty())
        ul3 = UnspacedList([])
        ul3.append(self.ul)
        self.assertEqual(False, self.ul.is_dirty())
        self.assertEqual(True, ul3.is_dirty())
        ul4 = UnspacedList([[1], [2, 3, 4]])
        self.assertEqual(False, ul4.is_dirty())
        ul4[1][2] = 5
        self.assertEqual(True, ul4.is_dirty())


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
