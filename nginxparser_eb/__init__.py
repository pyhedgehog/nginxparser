#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Forked from:
# - https://github.com/fatiherikli/nginxparser
# - CertBot Nginx parser

import string
import copy
import types
import logging
from pyparsing import (
    Literal, White, Word, alphanums, CharsNotIn, Combine, Forward, Group, SkipTo,
    Optional, OneOrMore, ZeroOrMore, pythonStyleComment, Regex)

import pyparsing
from pyparsing import stringEnd
from pyparsing import restOfLine


pyparsing.ParserElement.setDefaultWhitespaceChars(" \n\t\r")
logger = logging.getLogger(__name__)


class NginxParser(object):
    # pylint: disable=expression-not-assigned
    """A class that parses nginx configuration with pyparsing."""

    # constants
    space = Optional(White())
    nonspace = Regex(r"\S+")
    left_bracket = Literal("{").suppress()
    right_bracket = space.leaveWhitespace() + Literal("}").suppress()
    semicolon = Literal(";").suppress()
    key = Word(alphanums + "_/+-.")
    dollar_var = Combine(Literal('$') + Regex(r"[^\{\};,\s]+"))
    condition = Regex(r"\(.+\)")
    # Matches anything that is not a special character, and ${SHELL_VARS}, AND
    # any chars in single or double quotes
    # All of these COULD be upgraded to something like
    # https://stackoverflow.com/a/16130746
    dquoted = Regex(r'(\".*\")')
    squoted = Regex(r"(\'.*\')")
    nonspecial = Regex(r"[^\{\};,]")
    varsub = Regex(r"(\$\{\w+\})")
    # nonspecial nibbles one character at a time, but the other objects take
    # precedence.  We use ZeroOrMore to allow entries like "break ;" to be
    # parsed as assignments
    value = Combine(ZeroOrMore(dquoted | squoted | varsub | nonspecial))

    location = CharsNotIn("{};," + string.whitespace)
    # modifier for location uri [ = | ~ | ~* | ^~ ]
    modifier = Literal("=") | Literal("~*") | Literal("~") | Literal("^~")

    # rules
    comment = space + Literal('#') + restOfLine

    assignment = space + key + Optional(space + value, default=None) + semicolon
    location_statement = space + Optional(modifier) + Optional(space + location + space)
    if_statement = space + Literal("if") + space + condition + space
    charset_map_statement = space + Literal("charset_map") + space + value + space + value

    map_statement = space + Literal("map") + space + nonspace + space + dollar_var + space
    # This is NOT an accurate way to parse nginx map entries; it's almost
    # certainly too permissive and may be wrong in other ways, but it should
    # preserve things correctly in mmmmost or all cases.
    #
    #    - I can neither prove nor disprove that it is correct wrt all escaped
    #      semicolon situations
    # Addresses https://github.com/fatiherikli/nginxparser/issues/19
    map_pattern = Regex(r'".*"') | Regex(r"'.*'") | nonspace
    map_entry = space + map_pattern + space + value + space + semicolon
    map_block = Group(
        Group(map_statement).leaveWhitespace() +
        left_bracket +
        Group(ZeroOrMore(Group(comment | map_entry)) + space).leaveWhitespace() +
        right_bracket)

    block = Forward()

    # key could for instance be "server" or "http", or "location" (in which case
    # location_statement needs to have a non-empty location)

    block_begin = (Group(space + key + location_statement) ^
                   Group(if_statement) ^
                   Group(charset_map_statement)).leaveWhitespace()

    block_innards = Group(ZeroOrMore(Group(comment | assignment) | block | map_block)
                          + space).leaveWhitespace()

    block << Group(block_begin + left_bracket + block_innards + right_bracket)

    script = OneOrMore(Group(comment | assignment) ^ block ^ map_block) + space + stringEnd
    script.parseWithTabs().leaveWhitespace()

    def __init__(self, source):
        self.source = source

    def parse(self):
        """Returns the parsed tree."""
        return self.script.parseString(self.source)

    def as_list(self):
        """Returns the parsed tree as a list."""
        return self.parse().asList()


class NginxDumper(object):
    # pylint: disable=too-few-public-methods
    """A class that dumps nginx configuration from the provided tree."""
    def __init__(self, blocks):
        self.blocks = blocks

    def __iter__(self, blocks=None):
        """Iterates the dumped nginx content."""
        blocks = blocks or self.blocks
        for b0 in blocks:
            if isinstance(b0, str):
                yield b0
                continue
            b = copy.deepcopy(b0)
            if spacey(b[0]):
                yield b.pop(0) # indentation
                if not b:
                    continue
            key, values = b.pop(0), b.pop(0)

            if isinstance(key, list):
                yield "".join(key) + '{'
                for parameter in values:
                    for line in self.__iter__([parameter]): # negate "for b0 in blocks"
                        yield line
                yield '}'
            else:
                if isinstance(key, str) and key.strip() == '#':  # comment
                    yield key + values
                else:                                            # assignment
                    gap = ""
                    # Sometimes the parser has stuck some gap whitespace in here;
                    # if so rotate it into gap
                    if values and spacey(values):
                        gap = values
                        values = b.pop(0)
                    yield key + gap + values + ';'

    def __str__(self):
        """Return the parsed block as a string."""
        return ''.join(self)


# Shortcut functions to respect Python's serialization interface
# (like pyyaml, picker or json)

def loads(source):
    """Parses from a string.

    :param str source: The string to parse
    :returns: The parsed tree
    :rtype: list

    """
    return UnspacedList(NginxParser(source).as_list())


def load(_file):
    """Parses from a file.

    :param file _file: The file to parse
    :returns: The parsed tree
    :rtype: list

    """
    return loads(_file.read())


def dumps(blocks):
    """Dump to a string.

    :param UnspacedList blocks: The parsed tree
    :param int indentation: The number of spaces to indent
    :rtype: str

    """
    return str(NginxDumper(blocks.spaced))


def dump(blocks, _file):
    """Dump to a file.

    :param UnspacedList blocks: The parsed tree
    :param file _file: The file to dump to
    :param int indentation: The number of spaces to indent
    :rtype: NoneType

    """
    return _file.write(dumps(blocks))


class BaseDirective(object):
    """
    Simple representation for a config directive for Nginx
    """
    def __init__(self, key=None, value=None, parent=None, raw=None):
        self.key = key
        self.value = value
        self.parent = parent
        self.raw = raw

    def __repr__(self):
        return 'Base(key=%r, value=%r)' % (self.key, self.value)

    def __str__(self):
        return '%s -> %s' % (self.key, self.value)


class BlockDirective(BaseDirective):
    """
    Simple representation for a block with more directives
    """
    def __init__(self, key=None, value=None, parent=None, raw=None):
        super(BlockDirective, self).__init__(key, value, parent, raw)

    def __repr__(self):
        return 'Block(key=%r, dirs=%r)' % (self.key, self.value)


def build_model(cfg, parent=None):
    """
    Returns model version of the config
    :param cfg: 
    :param parent: 
    :return: 
    """
    # If not a list -> directive, return
    if not isinstance(cfg, types.ListType):
        return [BaseDirective(parent=parent, raw=cfg)]

    # Assume blocks.
    root = BlockDirective(value=[], parent=parent, raw=cfg)
    for sub in cfg:
        if not isinstance(sub, types.ListType):
            raise ValueError('Directive expected: %s' % sub)

        if isinstance(sub[1], types.ListType):
            sub_block = build_model(sub[1], parent=root)
            sub_block.key = sub[0]
            sub_block.raw = sub
            root.value.append(sub_block)

        else:
            sub_dir = BaseDirective(key=sub[0], value=sub[1], parent=root, raw=sub)
            root.value.append(sub_dir)

    return root


def rebuild_model(root):
    """
    Rebuilds model from the root, using raw
    :param root: 
    :return: 
    """
    return build_model(root.raw, None)


def find_in_model(model, path):
    """
    Finding elements defined by the path array in the configuration model.
    Model to search can be BlockDirective or a list
    :param model: 
    :param path: 
    :return: 
    """
    if path is None:
        path = []

    # End of the search, the whole path was reduced
    if len(path) == 0:
        return [model]

    # Assume blocks.
    ret_value = []
    target = model if isinstance(model, types.ListType) else model.value

    for sub in target:
        if sub.key == path[0] or sub.key == [path[0]]:
            if isinstance(sub, BlockDirective):
                ret_value += find_in_model(sub, path[1:])
            elif isinstance(sub, BaseDirective):
                ret_value += [sub]
            else:
                raise ValueError('Unexpected model type')

    return ret_value


def remove_from_model(root, element, rebuild=True):
    """
    Removes given element from the model.
    The root needs to be rebuild
    :param root: 
    :param element: 
    :param rebuild: 
    :return: new root 
    """
    if element.parent is None:
        raise ValueError('Cannot remove parentless entry')

    if element.raw not in element.parent.raw[1]:
        raise ValueError('Malformed model, element not present in the parent')

    idx = None
    for i, x in enumerate(element.parent.raw[1]):
        if x == element.raw:
            idx = i
            break

    if idx is None:
        raise ValueError('Not found')

    del element.parent.raw[1][idx]

    if rebuild:
        return rebuild_model(root)
    return root


def find_elems(cfg, path):
    """
    Finding elements defined by the path array.
    Returns simple parts of the configuration.
    :param cfg:
    :param path: [server, http, error_log]
    :return:
    """
    # If not a list -> directive, return
    if not isinstance(cfg, types.ListType):
        return [cfg]

    if path is None:
        path = []

    # End of the search, the whole path was reduced
    if len(path) == 0:
        return [cfg]

    # Assume blocks.
    ret_value = []
    for sub in cfg:
        if not isinstance(sub, types.ListType):
            raise ValueError('Directive expected: %s' % sub)

        if len(sub) != 2:
            logger.debug('Sub block has invalid length %s' % sub)
            continue

        if sub[0] == path[0] or sub[0] == [path[0]]:
            ret_value += find_elems(sub[1], path[1:])

    return ret_value


def spacey(x):
    return (isinstance(x, str) and x.isspace()) or x == ''


class UnspacedList(list):
    """Wrap a list [of lists], making any whitespace entries magically invisible"""

    def __init__(self, list_source):
        # ensure our argument is not a generator, and duplicate any sublists
        self.spaced = copy.deepcopy(list(list_source))
        self.dirty = False

        # Turn self into a version of the source list that has spaces removed
        # and all sub-lists also UnspacedList()ed
        list.__init__(self, list_source)
        for i, entry in reversed(list(enumerate(self))):
            if isinstance(entry, list):
                sublist = UnspacedList(entry)
                list.__setitem__(self, i, sublist)
                self.spaced[i] = sublist.spaced
            elif spacey(entry):
                # don't delete comments
                if "#" not in self[:i]:
                    list.__delitem__(self, i)

    def _coerce(self, inbound):
        """
        Coerce some inbound object to be appropriately usable in this object

        :param inbound: string or None or list or UnspacedList
        :returns: (coerced UnspacedList or string or None, spaced equivalent)
        :rtype: tuple

        """
        if not isinstance(inbound, list):                      # str or None
            return inbound, inbound
        else:
            if not hasattr(inbound, "spaced"):
                inbound = UnspacedList(inbound)
            return inbound, inbound.spaced

    def insert(self, i, x):
        item, spaced_item = self._coerce(x)
        slicepos = self._spaced_position(i) if i < len(self) else len(self.spaced)
        self.spaced.insert(slicepos, spaced_item)
        list.insert(self, i, item)
        self.dirty = True

    def append(self, x):
        item, spaced_item = self._coerce(x)
        self.spaced.append(spaced_item)
        list.append(self, item)
        self.dirty = True

    def extend(self, x):
        item, spaced_item = self._coerce(x)
        self.spaced.extend(spaced_item)
        list.extend(self, item)
        self.dirty = True

    def __add__(self, other):
        l = copy.deepcopy(self)
        l.extend(other)
        l.dirty = True
        return l

    def pop(self, _i=None):
        raise NotImplementedError("UnspacedList.pop() not yet implemented")

    def remove(self, _):
        raise NotImplementedError("UnspacedList.remove() not yet implemented")

    def reverse(self):
        raise NotImplementedError("UnspacedList.reverse() not yet implemented")

    def sort(self, _cmp=None, _key=None, _Rev=None):
        raise NotImplementedError("UnspacedList.sort() not yet implemented")

    def __setslice__(self, _i, _j, _newslice):
        raise NotImplementedError("Slice operations on UnspacedLists not yet implemented")

    def __setitem__(self, i, value):
        if isinstance(i, slice):
            raise NotImplementedError("Slice operations on UnspacedLists not yet implemented")
        item, spaced_item = self._coerce(value)
        self.spaced.__setitem__(self._spaced_position(i), spaced_item)
        list.__setitem__(self, i, item)
        self.dirty = True

    def __delitem__(self, i):
        self.spaced.__delitem__(self._spaced_position(i))
        list.__delitem__(self, i)
        self.dirty = True

    def __deepcopy__(self, memo):
        l = UnspacedList(self[:])
        l.spaced = copy.deepcopy(self.spaced, memo=memo)
        l.dirty = self.dirty
        return l

    def is_dirty(self):
        """Recurse through the parse tree to figure out if any sublists are dirty"""
        if self.dirty:
            return True
        return any((isinstance(x, list) and x.is_dirty() for x in self))

    def _spaced_position(self, idx):
        """Convert from indexes in the unspaced list to positions in the spaced one"""
        pos = spaces = 0
        # Normalize indexes like list[-1] etc, and save the result
        if idx < 0:
            idx = len(self) + idx
        if not 0 <= idx < len(self):
            raise IndexError("list index out of range")
        idx0 = idx
        # Count the number of spaces in the spaced list before idx in the unspaced one
        while idx != -1:
            if spacey(self.spaced[pos]):
                spaces += 1
            else:
                idx -= 1
            pos += 1
        return idx0 + spaces


