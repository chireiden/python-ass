from . import document, line, section
from .document import *  # noqa: F40
from .line import *  # noqa: F40
from .section import *  # noqa: F40

__all__ = [
    *document.__all__,
    *line.__all__,
    *section.__all__,
    "parse",
    "parse_file",
    "parse_string",
]

parse_file = document.Document.parse_file
parse_string = document.Document.parse_string
parse = parse_file
