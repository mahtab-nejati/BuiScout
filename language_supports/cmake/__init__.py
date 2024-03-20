from .conditional_def_use_chains import (
    ConditionalDefUseChains,
    CallableConditionalDefUseChains,
)
from .name_getter import NameGetter
from .stringifier import Stringifier
from .actor_getter import ActorGetter
from .extended_processor import ExtendedProcessor
from .unparser import Unparser

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
    '"',
    "",
]
BASIC_TYPES = [ROOT_TYPE]
