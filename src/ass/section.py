from collections import abc, OrderedDict

from .line import Unknown, Dialogue, Movie, Command, Sound, Picture, Comment, Style
from .data import _Field

__all__ = (
    'LineSection',
    'FieldSection',
    'EventsSection',
    'StylesSection',
    'ScriptInfoSection',
)


class LineSection(abc.MutableSequence):
    FORMAT_TYPE = "Format"
    line_parsers = None
    field_order = None

    def __init__(self, name, lines=None):
        self.name = name
        self._lines = [] if lines is None else lines

    def dump(self):
        yield "[{}]".format(self.name)

        if self.field_order is not None:
            yield "{}: {}".format(LineSection.FORMAT_TYPE, ", ".join(self.field_order))

        for line in self._lines:
            yield line.dump_with_type(self.field_order)

    def add_line(self, type_name, raw_line):
        # field order is optional
        if type_name.lower() == LineSection.FORMAT_TYPE.lower():
            self.field_order = [field.strip() for field in raw_line.split(",")]
        else:
            if self.line_parsers is not None and type_name.lower() not in self.line_parsers:
                raise ValueError("unexpected {} line in {}".format(type_name, self.name))

            parser = (self.line_parsers[type_name.lower()]
                      if self.line_parsers is not None
                      else Unknown)
            self._lines.append(parser.parse(type_name, raw_line, self.field_order))

    def set_data(self, lines):
        if not isinstance(lines, abc.MutableSequence):
            raise ValueError("Lines must be a mutable list")
        self._lines = lines

    def __getitem__(self, index):
        return self._lines[index]

    def __setitem__(self, index, val):
        self._lines[index] = val

    def __delitem__(self, index):
        del self._lines[index]

    def __len__(self):
        return len(self._lines)

    def insert(self, index, val):
        self._lines.insert(index, val)

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.name, self._lines)


class FieldSection(abc.MutableMapping):
    # avoid metaclass conflict by keeping track of fields in a dict instead
    FIELDS = {}

    def __init__(self, name, fields=None):
        self.name = name
        self._fields = OrderedDict() if fields is None else fields

    def add_line(self, field_name, field):
        if field_name in self.FIELDS:
            field = self.FIELDS[field_name].parse(field)

        self._fields[field_name] = field

    def dump(self):
        yield "[{}]".format(self.name)

        for k, v in self._fields.items():
            yield "{}: {}".format(k, _Field.dump(v))

    def set_data(self, fields):
        if not isinstance(fields, abc.MutableMapping):
            raise ValueError("Fields must be a mutable mapping")
        self._fields = fields

    def __contains__(self, key):
        return key in self._fields

    def __getitem__(self, key):
        return self._fields[key]

    def __setitem__(self, key, value):
        self._fields[key] = value

    def __delitem__(self, key):
        del self._fields[key]

    def __iter__(self):
        return iter(self._fields)

    def __len__(self):
        return len(self._fields)

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.name, self._fields)

    def clear(self):  # Optional, but should be faster this way
        return self._fields.clear()

    def copy(self):
        return self.__class__(self.name, self._fields.copy())


class EventsSection(LineSection):
    field_order = Dialogue.DEFAULT_FIELD_ORDER
    line_parsers = {
        "dialogue": Dialogue,  # noqa: E241
        "comment":  Comment,   # noqa: E241
        "picture":  Picture,   # noqa: E241
        "sound":    Sound,     # noqa: E241
        "movie":    Movie,     # noqa: E241
        "command":  Command    # noqa: E241
    }


class StylesSection(LineSection):
    field_order = Style.DEFAULT_FIELD_ORDER
    line_parsers = {
        "style": Style
    }


class ScriptInfoSection(FieldSection):
    VERSION_ASS = "v4.00+"
    VERSION_SSA = "v4.00"
    FIELDS = {
        "ScriptType": _Field("ScriptType", str, default=VERSION_ASS),
        "PlayResX": _Field("PlayResX", int, default=640),
        "PlayResY": _Field("PlayResY", int, default=480),
        "WrapStyle": _Field("WrapStyle", int, default=0),
        "ScaledBorderAndShadow": _Field("ScaledBorderAndShadow", str, default="yes")
    }
