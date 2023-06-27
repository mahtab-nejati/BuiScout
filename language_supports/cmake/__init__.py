from .def_use_chains import DefUseChains
from .name_getter import NameGetter
from .stringifier import Stringifier
from .actor_getter import ActorGetter

ROOT_TYPE = "source_file"
# Nodes of type listed in IGNORED_TYPES
# and their entire subtree are ignored
IGNORED_TYPES = [
    "bracket_comment",
    "line_comment",
    "(",
    ")",
    "{",
    "}",
    "<",
    ">",
    "\\n",
    "\\t",
    "$",
    ";",
    ":",
    "quotation",
    "",
]
BASIC_TYPES = [ROOT_TYPE]
