from datetime import timedelta

from .data import Color, _WithFieldMeta, _Field

__all__ = (
    'Unknown',
    'Style',
    'Dialogue',
    'Comment',
    'Comment',
    'Picture',
    'Sound',
    'Movie',
)


class _Line(object, metaclass=_WithFieldMeta):
    # to be overridden in subclasses or through the type_name argument
    # TODO remove; it's primarily kept for backwards compat but not good architecture
    TYPE = None

    def __init__(self, *args, type_name=None, **kwargs):
        self.fields = {f.name: f.default for f in self._field_defs}

        for k, v in zip(self.DEFAULT_FIELD_ORDER, args):
            self.fields[k] = v

        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.fields[k] = v

        if self.TYPE is None:
            self.TYPE = type_name

    def dump(self, field_order=None):
        """ Dump an ASS line into text format. Has an optional field order
        parameter in case you have some wonky format.
        """
        if field_order is None:
            field_order = self.DEFAULT_FIELD_ORDER

        return ",".join(_Field.dump(self.fields[field])
                        for field in field_order)

    def dump_with_type(self, field_order=None):
        """ Dump an ASS line into text format, with its type prepended. """
        return self.TYPE + ": " + self.dump(field_order)

    @classmethod
    def parse(cls, type_name, line, field_order=None):
        """ Parse an ASS line from text format. Has an optional field order
        parameter in case you have some wonky format.
        """
        if field_order is None:
            field_order = cls.DEFAULT_FIELD_ORDER

        parts = line.split(",", len(field_order) - 1)

        if len(parts) != len(field_order):
            raise ValueError("arity of line does not match arity of field order")

        fields = {}

        for field_name, field in zip(field_order, parts):
            if field_name in cls._field_mappings:
                field = cls._field_mappings[field_name].parse(field)
            fields[field_name] = field

        return cls(**fields, type_name=type_name)

    def __repr__(self):
        params = ", ".join("{}={!r}".format(self._field_attributes[name], self.fields[name])
                           for name in self.DEFAULT_FIELD_ORDER)
        return "{}({})".format(self.__class__.__name__, params)


class Unknown(_Line):
    value = _Field("Value", str, default="")


class Style(_Line):
    """ A style line in ASS.
    """
    TYPE = "Style"

    name = _Field("Name", str, default="Default")
    fontname = _Field("Fontname", str, default="Arial")
    fontsize = _Field("Fontsize", float, default=20)
    primary_color = _Field("PrimaryColour", Color, default=Color.WHITE)
    secondary_color = _Field("SecondaryColour", Color, default=Color.RED)
    outline_color = _Field("OutlineColour", Color, default=Color.BLACK)
    back_color = _Field("BackColour", Color, default=Color.BLACK)
    bold = _Field("Bold", bool, default=False)
    italic = _Field("Italic", bool, default=False)
    underline = _Field("Underline", bool, default=False)
    strike_out = _Field("StrikeOut", bool, default=False)
    scale_x = _Field("ScaleX", float, default=100)
    scale_y = _Field("ScaleY", float, default=100)
    spacing = _Field("Spacing", float, default=0)
    angle = _Field("Angle", float, default=0)
    border_style = _Field("BorderStyle", int, default=1)
    outline = _Field("Outline", float, default=2)
    shadow = _Field("Shadow", float, default=2)
    alignment = _Field("Alignment", int, default=2)
    margin_l = _Field("MarginL", int, default=10)
    margin_r = _Field("MarginR", int, default=10)
    margin_v = _Field("MarginV", int, default=10)
    encoding = _Field("Encoding", int, default=1)


class _Event(_Line):
    layer = _Field("Layer", int, default=0)
    start = _Field("Start", timedelta, default=timedelta(0))
    end = _Field("End", timedelta, default=timedelta(0))
    style = _Field("Style", str, default="Default")
    name = _Field("Name", str, default="")
    margin_l = _Field("MarginL", int, default=0)
    margin_r = _Field("MarginR", int, default=0)
    margin_v = _Field("MarginV", int, default=0)
    effect = _Field("Effect", str, default="")
    text = _Field("Text", str, default="")


class Dialogue(_Event):
    """ A dialog event.
    """
    TYPE = "Dialogue"


class Comment(_Event):
    """ A comment event.
    """
    TYPE = "Comment"


class Picture(_Event):
    """ A picture event. Not widely supported.
    """
    TYPE = "Picture"


class Sound(_Event):
    """ A sound event. Not widely supported.
    """
    TYPE = "Sound"


class Movie(_Event):
    """ A movie event. Not widely supported.
    """
    TYPE = "Movie"


class Command(_Event):
    """ A command event. Not widely supported.
    """
    TYPE = "Command"
