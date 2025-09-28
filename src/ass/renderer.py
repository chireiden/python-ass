import ctypes
import ctypes.util

from datetime import timedelta

_libass = ctypes.cdll.LoadLibrary(ctypes.util.find_library("ass"))
_libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("c"))


class ImageSequence(object):
    def __init__(self, renderer, head_ptr):
        self.renderer = renderer
        self.head_ptr = head_ptr

    def __iter__(self):
        cur = self.head_ptr
        while cur:
            yield cur.contents
            cur = cur.contents.next_ptr


class Image(ctypes.Structure):
    TYPE_CHARACTER = 0
    TYPE_OUTLINE = 1
    TYPE_SHADOW = 2

    @property
    def rgba(self):
        color = self.color

        a = color & 0xff
        color >>= 8

        b = color & 0xff
        color >>= 8

        g = color & 0xff
        color >>= 8

        r = color & 0xff

        return (r, g, b, a)

    def __getitem__(self, loc):
        x, y = loc
        return ord(self.bitmap[y * self.stride + x])


Image._fields_ = [
    ("w", ctypes.c_int),
    ("h", ctypes.c_int),
    ("stride", ctypes.c_int),
    ("bitmap", ctypes.POINTER(ctypes.c_char)),
    ("color", ctypes.c_uint32),
    ("dst_x", ctypes.c_int),
    ("dst_y", ctypes.c_int),
    ("next_ptr", ctypes.POINTER(Image)),
    ("type", ctypes.c_int)
]


def _make_libass_setter(name, types):
    fun = _libass[name]
    fun.argtypes = [ctypes.c_void_p] + types

    def setter(self, v):
        if len(types) == 1:
            fun(ctypes.byref(self), v)
        else:
            fun(ctypes.byref(self), *v)
        self._internal_fields[name] = v

    return setter


def _make_libass_property(name, types):
    def getter(self):
        return self._internal_fields.get(name)

    return property(getter, _make_libass_setter(name, types))


class Context(ctypes.Structure):
    def __new__(self):
        return _libass.ass_library_init().contents

    def __init__(self):
        self._internal_fields = {}

        self._style_overrides_buffers = []

        if not ctypes.byref(self):
            raise RuntimeError("could not initialize libass")

        self.extract_fonts = False
        self.style_overrides = []

    def __del__(self):
        _libass.ass_library_done(ctypes.byref(self))

    fonts_dir = _make_libass_property("ass_set_fonts_dir", [
        ctypes.c_char_p
    ])
    extract_fonts = _make_libass_property("ass_set_extract_fonts", [
        ctypes.c_int
    ])

    @property
    def style_overrides(self):
        return [buf.value for buf in self._style_overrides_buffers]

    @style_overrides.setter
    def style_overrides(self, xs):
        self._style_overrides_buffers = [ctypes.create_string_buffer(x)
                                         for x in xs]

        if self._style_overrides_buffers:
            ptr = (ctypes.c_char_p * len(self._style_overrides_buffers))(*[
                ctypes.addressof(buf)
                for buf in self._style_overrides_buffers
            ])
        else:
            ptr = ctypes.POINTER(ctypes.c_char_p)()

        _libass.ass_set_style_overrides(
            ctypes.byref(self),
            ptr)

    def make_renderer(self):
        """ Make a renderer instance for rendering tracks. """
        renderer = _libass.ass_renderer_init(ctypes.byref(self)).contents
        renderer._after_init(self)
        return renderer

    def parse_to_track(self, data, codepage="UTF-8"):
        """ Parse ASS data to a track. """
        return _libass.ass_read_memory(ctypes.byref(self), data, len(data),
                                       codepage.encode("utf-8")).contents

    def make_track(self):
        track = _libass.ass_new_track(ctypes.byref(self)).contents
        track._after_init(self)
        return track


class Renderer(ctypes.Structure):
    SHAPING_SIMPLE = 0
    SHAPING_COMPLEX = 1

    HINTING_NONE = 0
    HINTING_LIGHT = 1
    HINTING_NORMAL = 2
    HINTING_NATIVE = 3

    def _after_init(self, ctx):
        self._ctx = ctx
        self._fonts_set = False
        self._internal_fields = {}

        self.frame_size = (640, 480)
        self.storage_size = (640, 480)
        self.margins = (0, 0, 0, 0)
        self.use_margins = True
        self.font_scale = 1
        self.line_spacing = 0
        self.pixel_aspect = 1.0

    def __del__(self):
        _libass.ass_renderer_done(ctypes.byref(self))

    frame_size = _make_libass_property("ass_set_frame_size", [
        ctypes.c_int,
        ctypes.c_int
    ])
    storage_size = _make_libass_property("ass_set_storage_size", [
        ctypes.c_int,
        ctypes.c_int
    ])
    shaper = _make_libass_property("ass_set_shaper", [
        ctypes.c_int
    ])
    margins = _make_libass_property("ass_set_margins", [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int
    ])
    use_margins = _make_libass_property("ass_set_use_margins", [
        ctypes.c_int
    ])
    pixel_aspect = _make_libass_property("ass_set_pixel_aspect", [
        ctypes.c_double
    ])
    aspect_ratio = _make_libass_property("ass_set_aspect_ratio", [
        ctypes.c_double,
        ctypes.c_double
    ])
    font_scale = _make_libass_property("ass_set_font_scale", [
        ctypes.c_double
    ])
    hinting = _make_libass_property("ass_set_hinting", [
        ctypes.c_int
    ])
    line_spacing = _make_libass_property("ass_set_line_spacing", [
        ctypes.c_double
    ])
    line_position = _make_libass_property("ass_set_line_position", [
        ctypes.c_double
    ])

    def set_fonts(self, default_font=None, default_family=None,
                  fontconfig_config=None, update_fontconfig=None):
        fc = fontconfig_config is not None

        if update_fontconfig is None:
            update_fontconfig = fontconfig_config is not None

        if default_font is not None:
            default_font = default_font.encode("utf-8")

        if default_family is not None:
            default_family = default_family.encode("utf-8")

        _libass.ass_set_fonts(ctypes.byref(self), default_font, default_family,
                              fc, fontconfig_config.encode("utf-8") or "",
                              update_fontconfig)
        self._fonts_set = True

    def update_fonts(self):
        if not self._fonts_set:
            raise RuntimeError("set_fonts before updating them")
        _libass.ass_fonts_update(ctypes.byref(self))

    set_cache_limits = _make_libass_setter("ass_set_cache_limits", [
        ctypes.c_int,
        ctypes.c_int
    ])

    @staticmethod
    def timedelta_to_ms(td):
        return int(td.total_seconds()) * 1000 + td.microseconds // 1000

    def render_frame(self, track, now):
        if not self._fonts_set:
            raise RuntimeError("set_fonts before rendering")
        head = _libass.ass_render_frame(ctypes.byref(self),
                                        ctypes.byref(track),
                                        Renderer.timedelta_to_ms(now),
                                        ctypes.POINTER(ctypes.c_int)())
        return ImageSequence(self, head)

    def set_all_sizes(self, size):
        self.frame_size = size
        self.storage_size = size
        self.pixel_aspect = 1.0


class Style(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char_p),
        ("fontname", ctypes.c_char_p),
        ("fontsize", ctypes.c_double),
        ("primary_color", ctypes.c_uint32),
        ("secondary_color", ctypes.c_uint32),
        ("outline_color", ctypes.c_uint32),
        ("back_color", ctypes.c_uint32),
        ("bold", ctypes.c_int),
        ("italic", ctypes.c_int),
        ("underline", ctypes.c_int),
        ("strike_out", ctypes.c_int),
        ("scale_x", ctypes.c_double),
        ("scale_y", ctypes.c_double),
        ("spacing", ctypes.c_double),
        ("angle", ctypes.c_double),
        ("border_style", ctypes.c_int),
        ("outline", ctypes.c_double),
        ("shadow", ctypes.c_double),
        ("alignment", ctypes.c_int),
        ("margin_l", ctypes.c_int),
        ("margin_r", ctypes.c_int),
        ("margin_v", ctypes.c_int),
        ("encoding", ctypes.c_int),
        ("treat_fontname_as_pattern", ctypes.c_int),
        ("blur", ctypes.c_double)
    ]

    @staticmethod
    def numpad_align(val):
        v = (val - 1) // 3
        if v != 0:
            v = 3 - v
        res = ((val - 1) % 3) + 1
        res += v * 4
        return res

    def _after_init(self, track):
        self._track = track

    def populate(self, style):
        self.name = style.name.encode("utf-8")
        self.fontname = style.fontname.encode("utf-8")
        self.fontsize = style.fontsize
        self.primary_color = style.primary_color.to_int()
        self.secondary_color = style.secondary_color.to_int()
        self.outline_color = style.outline_color.to_int()
        self.back_color = style.back_color.to_int()
        self.bold = style.bold
        self.italic = style.italic
        self.underline = style.underline
        self.strike_out = style.strike_out
        self.scale_x = style.scale_x / 100.0
        self.scale_y = style.scale_y / 100.0
        self.spacing = style.spacing
        self.angle = style.angle
        self.border_style = style.border_style
        self.outline = style.outline
        self.shadow = style.shadow
        self.alignment = Style.numpad_align(style.alignment)
        self.margin_l = style.margin_l
        self.margin_r = style.margin_r
        self.margin_v = style.margin_v
        self.encoding = style.encoding


class Event(ctypes.Structure):
    _fields_ = [
        ("start_ms", ctypes.c_longlong),
        ("duration_ms", ctypes.c_longlong),
        ("read_order", ctypes.c_int),
        ("layer", ctypes.c_int),
        ("style_id", ctypes.c_int),
        ("name", ctypes.c_char_p),
        ("margin_l", ctypes.c_int),
        ("margin_r", ctypes.c_int),
        ("margin_v", ctypes.c_int),
        ("effect", ctypes.c_char_p),
        ("text", ctypes.c_char_p),
        ("render_priv", ctypes.c_void_p)
    ]

    def _after_init(self, track):
        self._track = track

    @property
    def start(self):
        return timedelta(milliseconds=self.start_ms)

    @start.setter
    def start(self, td):
        self.start_ms = Renderer.timedelta_to_ms(td)

    @property
    def duration(self):
        return timedelta(milliseconds=self.duration_ms)

    @duration.setter
    def duration(self, td):
        self.duration_ms = Renderer.timedelta_to_ms(td)

    @property
    def style(self):
        return self._track.styles[self.style_id].name

    @style.setter
    def style(self, v):
        # NOTE: linear time every time we want to add a style
        for i, style in enumerate(self._track.styles):
            if style.name == v.encode("utf-8"):
                self.style_id = i
                return

        raise ValueError("style not found")

    def populate(self, event):
        self.start = event.start
        self.duration = event.end - event.start
        self.layer = event.layer
        self.style = event.style
        self.name = event.name.encode("utf-8")
        self.margin_l = event.margin_l
        self.margin_r = event.margin_r
        self.margin_v = event.margin_v
        self.effect = event.effect.encode("utf-8")
        self.text = event.text.encode("utf-8")


class Track(ctypes.Structure):
    TYPE_UNKNOWN = 0
    TYPE_ASS = 1
    TYPE_SSA = 2

    _fields_ = [
        ("n_styles", ctypes.c_int),
        ("max_styles", ctypes.c_int),
        ("n_events", ctypes.c_int),
        ("max_events", ctypes.c_int),
        ("styles_arr", ctypes.POINTER(Style)),
        ("events_arr", ctypes.POINTER(Event)),
        ("style_format", ctypes.c_char_p),
        ("event_format", ctypes.c_char_p),
        ("track_type", ctypes.c_int),
        ("play_res_x", ctypes.c_int),
        ("play_res_y", ctypes.c_int),
        ("timer", ctypes.c_double),
        ("wrap_style", ctypes.c_int),
        ("scaled_border_and_shadow", ctypes.c_int),
        ("kerning", ctypes.c_int),
        ("language", ctypes.c_char_p),
        ("ycbcr_matrix", ctypes.c_int),
        ("default_style", ctypes.c_int),
        ("name", ctypes.c_char_p),
        ("library", ctypes.POINTER(Context)),
        ("parser_priv", ctypes.c_void_p)
    ]

    def _after_init(self, ctx):
        self._ctx = ctx

    @property
    def styles(self):
        if self.n_styles == 0:
            return []
        return ctypes.cast(self.styles_arr,
                           ctypes.POINTER(Style * self.n_styles)).contents

    @property
    def events(self):
        if self.n_events == 0:
            return []
        return ctypes.cast(self.events_arr,
                           ctypes.POINTER(Event * self.n_events)).contents

    def make_style(self):
        style = self.styles_arr[_libass.ass_alloc_style(ctypes.byref(self))]
        style._after_init(self)
        return style

    def make_event(self):
        event = self.events_arr[_libass.ass_alloc_event(ctypes.byref(self))]
        event._after_init(self)
        return event

    def __del__(self):
        # XXX: we can't use ass_free_track because it assumes we've allocated
        #      our strings in the heap (wat), so we just free them with libc.
        _libc.free(self.styles_arr)
        _libc.free(self.events_arr)
        _libc.free(ctypes.byref(self))

    def populate(self, doc):
        """ Convert an ASS document to a track. """
        self.type = Track.TYPE_ASS

        self.play_res_x = doc.play_res_x
        self.play_res_y = doc.play_res_y
        self.wrap_style = doc.wrap_style
        self.scaled_border_and_shadow = (doc.scaled_border_and_shadow.lower() == "yes")

        self.style_format = ", ".join(doc.SECTIONS[doc.STYLE_ASS_HEADER].field_order).encode()
        self.event_format = ", ".join(doc.SECTIONS[doc.EVENTS_HEADER].field_order).encode()

        for d_style in doc.styles:
            style = self.make_style()
            style.populate(d_style)

        for d_event in doc.events:
            if d_event.TYPE != "Dialogue":
                continue
            event = self.make_event()
            event.populate(d_event)


_libc.free.argtypes = [ctypes.c_void_p]

_libass.ass_library_init.restype = ctypes.POINTER(Context)

_libass.ass_library_done.argtypes = [ctypes.POINTER(Context)]

_libass.ass_renderer_init.argtypes = [ctypes.POINTER(Context)]
_libass.ass_renderer_init.restype = ctypes.POINTER(Renderer)

_libass.ass_renderer_done.argtypes = [ctypes.POINTER(Renderer)]

_libass.ass_new_track.argtypes = [ctypes.POINTER(Context)]
_libass.ass_new_track.restype = ctypes.POINTER(Track)

_libass.ass_set_style_overrides.argtypes = [
    ctypes.POINTER(Context),
    ctypes.POINTER(ctypes.c_char_p)
]
_libass.ass_set_fonts.argtypes = [
    ctypes.POINTER(Renderer),
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_int
]
_libass.ass_fonts_update.argtypes = [ctypes.POINTER(Renderer)]

_libass.ass_render_frame.argtypes = [
    ctypes.POINTER(Renderer),
    ctypes.POINTER(Track),
    ctypes.c_longlong,
    ctypes.POINTER(ctypes.c_int)
]
_libass.ass_render_frame.restype = ctypes.POINTER(Image)

_libass.ass_read_memory.argtypes = [
    ctypes.POINTER(Context),
    ctypes.c_char_p,
    ctypes.c_size_t,
    ctypes.c_char_p
]
_libass.ass_read_memory.restype = ctypes.POINTER(Track)

_libass.ass_alloc_style.argtypes = [ctypes.POINTER(Track)]
_libass.ass_alloc_style.restype = ctypes.c_int

_libass.ass_alloc_event.argtypes = [ctypes.POINTER(Track)]
_libass.ass_alloc_event.restype = ctypes.c_int
