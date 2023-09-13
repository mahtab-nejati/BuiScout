from .conditional_def_use_chains import DefUseChains
from .name_getter import NameGetter
from .actor_getter import ActorGetter
from .stringifier import Stringifier

ROOT_TYPE = "source_file"
# Nodes of type listed in IGNORED_TYPES
# and their entire subtree are ignored
IGNORED_TYPES = []

BASIC_TYPES = [ROOT_TYPE]
