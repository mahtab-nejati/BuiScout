from utils.visitors import NodeVisitor
import data_flow_analysis.chain_model as cm


ROOT_TYPE = "source_file"
# Nodes of type listed in IGNORED_TYPES
# and their entire subtree are ignored
IGNORED_TYPES = []
BASIC_TYPES = []

BUILTIN_COMMANDS = []


class NameGetter(NodeVisitor):
    pass

class DefUseChains(cm.DefUseChains):
    pass
    
def stringify(ast, node_data, verbose=False, *args, **kwargs):
    pass